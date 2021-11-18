#!/usr/bin/env python

from __future__ import annotations
from typing import *
from copy import *

from . import ir3
from . import iropt
from . import cglower
from . import cgpseudo
from . import cgliveness
from .util import Location, TCException, CGException, StringView, print_warning, escape_string



# func -> (assignments, spills, reg_live_ranges)
def allocate_registers(func: ir3.FuncDefn) -> Tuple[Dict[str, str], Set[str], Dict[str, Set[int]]]:
	# this wrapper only exists so that we lower functions exactly once.
	cglower.lower_function(func)
	return alloc_function(func)


def alloc_function(func: ir3.FuncDefn, prespilled: Set[str] = set()) -> Tuple[Dict[str, str], Set[str], Dict[str, Set[int]]]:
	stmts = iropt.renumber_statements(func)
	ins, outs, defs, uses = cgliveness.analyse(func, stmts)

	preds = iropt.compute_predecessors(func)

	# print(f"func: {func.name}")
	# for blk in func.blocks:
	# 	print(f">> {blk.name}")
	# 	for s in blk.stmts:
	# 		print(f"{s.id:02}  {s}     -- {preds[s.id]}")
	# 		print(f"  in =  {ins[s.id]}")
	# 		print(f"  out = {outs[s.id]}")

	# print("\n\n")
	"""
	TODO: do we need to consider OUT for def? the idea here is that, if we have the following:
	0:  z = 69;
	1:  ...
	2:  k = z + 7;
	3:  ...
	4:  k = k + 1;

	without considering OUT, we have live(z) = { 1, 2 }, live(k) = { 3, 4 }
	z and k here would *not* interfere. BUT, they actually don't -- nothing stops us
	from assigning the same register to `k` and `z`.
	if, in a subsequent line:

	5:  ...
	6:  y = z + 1;

	then, live(z) = { 1, 2, 3, 4, 5, 6 }, which would interfere with live(k) = { 3, 4 } --
	so it seems to suggest that we only need to consider IN.
	"""

	live_ranges: Dict[str, Set[int]] = dict()

	for n, vs in enumerate(ins):
		for v in vs:
			live_ranges.setdefault(v, set()).add(n)

	graph = Graph()

	# setup the nodes first.
	for var in live_ranges:
		graph.add(var)

	# now detect the interference. i guess the easiest way to do this is to get every pair of defs
	pairs = [(a, b) for a in live_ranges for b in live_ranges]
	for a, b in pairs:
		if a == b:
			continue

		# we iterate every (a, b) as well as (b, a), so the graph is bidirectional.
		if len(live_ranges[a].intersection(live_ranges[b])) > 0:
			graph.interfere(a, b)


	# `uses` now is (essentially) a map from stmt_num -> used_vars
	# we want to invert it.
	var_uses: Dict[str, Set[int]] = dict()
	for n, us in enumerate(uses):
		for u in us:
			var_uses.setdefault(u, set()).add(n)

	# same deal for `defs`
	var_defs: Dict[str, Set[int]] = dict()
	for n, ds in enumerate(defs):
		for d in ds:
			var_defs.setdefault(d, set()).add(n)


	# indicate preferences for the incoming arguments (which are not shadowed by locals) as a1-a4.
	# the value is a dict from register -> num_prefs (ie. how many times it was preferred)
	preassigned_tmp: Dict[str, Dict[str, int]] = dict()
	first_four_args: Set[str] = set()

	for i, param in enumerate(func.params[:4]):
		# only if it's not shadowed.
		if param.name not in func.vars:
			reg_name = f"a{i + 1}"
			preassigned_tmp.setdefault(param.name, dict()).setdefault(reg_name, 0)
			preassigned_tmp[param.name][reg_name] += 1

			first_four_args.add(param.name)


	# we also want to let variables sit in a nice register for function *calls* inside this body.
	for blk in func.blocks:
		for stmt in blk.stmts:
			call: Optional[ir3.FnCall] = None

			if isinstance(stmt, ir3.FnCallStmt):
				call = stmt.call

			elif isinstance(stmt, ir3.AssignOp) or isinstance(stmt, ir3.AssignDotOp):
				if isinstance(stmt.rhs, ir3.FnCallExpr):
					call = stmt.rhs.call

			if call is not None:
				# only consider the first 4 args (since they're the ones in registers)
				for i, arg in enumerate(call.args[:4]):
					if not isinstance(arg, ir3.VarRef):
						continue

					reg_name = f"a{i + 1}"
					preassigned_tmp.setdefault(arg.name, dict()).setdefault(reg_name, 0)
					preassigned_tmp[arg.name][reg_name] += 1


	# make the preassigns but unique the preferences, sorting by count.
	preassigned: Dict[str, List[str]] = dict()

	for var in preassigned_tmp:
		# note: negate the key to put the largest one first.
		regs: Iterable = sorted(preassigned_tmp[var].items(), key = lambda x: -x[1])
		regs = map(lambda x: x[0], regs)
		preassigned[var] = list(regs)


	registers = ["v1", "v2", "v3", "v4", "v5", "a1", "a2", "a3", "a4", "fp"]

	# print(f"\nprespilled = {prespilled}")
	# print(f"ranges: { {k: v  for k, v in map(lambda k: (k, live_ranges[k]), prespilled) } }")
	assigns, spills, retry = colour_graph(graph, registers, var_uses, live_ranges, preassigned, prespilled)
	if retry:
		# now we must spill the new variable.
		assert len(spills) == 1
		var = next(iter(spills))

		if var in prespilled:
			raise CGException(f"invalid double spill of '{var}', graph = {graph.edges}")

		# because of the way the blocks are structured and stuff, there isn't really a better way to do this.
		u_stmts = var_uses[var]
		d_stmts = var_defs[var]

		for blk in func.blocks:
			backup = copy(blk.stmts)
			blk.stmts = []
			for s in backup:
				if (s.id in u_stmts) and (s.id in d_stmts):
					blk.stmts.append(cgpseudo.RestoreVariable(s.loc, var))
					blk.stmts.append(s)
					blk.stmts.append(cgpseudo.SpillVariable(s.loc, var))

				elif s.id in u_stmts:
					blk.stmts.append(cgpseudo.RestoreVariable(s.loc, var))
					blk.stmts.append(s)

				elif s.id in d_stmts:
					blk.stmts.append(s)

					# if the var is one of the first 4 params and it is *not* shadowed,
					# then we also need to spill it. for 5+ params we spill back to the
					# callee-frame anyway, so an additional spill here is pointless
					# for local vars, they start with an indeterminate value, so spilling
					# is also pointless.
					if s.id != 0 or var in first_four_args:
						blk.stmts.append(cgpseudo.SpillVariable(s.loc, var))

				else:
					blk.stmts.append(s)

		return alloc_function(func, prespilled.union(spills))


	spills.update(prespilled)


	# the statements where the register is live. we just compute this from the assignment.
	reg_live_ranges: Dict[str, Set[int]] = { k: set() for k in registers }
	for var in assigns:
		# reg_live_ranges[assigns[var]] = set(range(0, len(stmts)))
		reg_live_ranges.setdefault(assigns[var], set()).update(live_ranges[var])


	# print(f"assigns = {assigns}")
	# print(f"spills = {spills}")

	return assigns, spills, reg_live_ranges



def colour_graph(graph_: Graph, registers: List[str], uses: Dict[str, Set[int]], live_ranges: Dict[str, Set[int]],
	preassigned: Dict[str, List[str]], prespilled_: Set[str]) -> Tuple[Dict[str, str], Set[str], bool]:

	graph = deepcopy(graph_)
	prespilled = copy(prespilled_)

	stack: List[str] = []
	preassigned_vars = set(preassigned.keys())

	while len(graph.get_remaining_nodes()) > 0:
		# we can't select preassigned vars to simplify.
		sel = graph.get_simplifiable_node(len(registers), exclude = preassigned_vars)

		if sel is not None:
			graph.remove(sel)
			stack.append(sel)
			prespilled.discard(sel)

		else:
			# try again, but without excluding preassigned nodes. this moves them
			# as far back as possible so they are more likely to get their colour.
			sel = graph.get_simplifiable_node(len(registers), exclude = set())
			if sel is not None:
				graph.remove(sel)
				stack.append(sel)
				prespilled.discard(sel)
				continue

			"""
			choose a node to spill. we have a few heuristics to use:
			1. its degree, ie. how many other vars it interferes with
				spilling such a variable would make colouring easier later on.
			2. how many times it is used
				spilling such a variable would be bad, because we need to touch memory more.
			3. the size of its live range. we actually want to prefer spilling stuff with
				a bigger live range, so this goes in the denominator.
			"""

			def get_spill_cost(var: str) -> float:
				return len(uses[var]) / (len(live_ranges[var]) + graph.get_degree(var))

			remaining_unspilled = graph.get_remaining_nodes() - prespilled
			foo: Iterable = map(lambda x: (x, get_spill_cost(x)), remaining_unspilled)
			foo = sorted(foo, key = lambda x: x[0])     # sort by name, so we get a reproducible spill order
			foo = list(foo)

			foo.sort(key = lambda x: x[1])

			if len(foo) > 0:
				# now get the first one
				sel = foo[0][0]
				# print(f"spilling {sel}")

				graph.remove(sel)
				stack.append(sel)

			else:
				if len(remaining_unspilled) == 0:
					break

				print(f"graph = {graph.edges}")
				raise CGException("failed to codegen: could not simplify interference graph")


	assignments: Dict[str, str] = dict()

	# process the prespilled ones first.
	for ps in prespilled:
		graph.remove(ps)
		stack.append(ps)

	while len(stack) > 0:
		var = stack.pop(len(stack) - 1)
		graph.unremove(var)
		neighbours = graph.get_neighbours(var)

		used_regs = set(map(lambda x: assignments[x], neighbours))
		free_regs = list(filter(lambda x: x not in used_regs, registers))

		if len(free_regs) > 0:

			# preassignment is just a preference; no guarantees.
			assigned = False
			if var in preassigned:
				for pref in preassigned[var]:
					if pref in free_regs:
						assignments[var] = pref
						assigned = True
						break

			if not assigned:
				assignments[var] = free_regs[0]

		else:
			# oops, we *really* need to spill.
			return dict(), set([ var ]), True


	return assignments, prespilled, False




class Graph:
	def __init__(self) -> None:
		self.edges: Dict[str, Set[str]] = dict()
		self.removed: Set[str] = set()

	def add(self, var: str) -> None:
		self.edges[var] = set()

	def interfere(self, a: str, b: str) -> None:
		self.edges[a].add(b)
		self.edges[b].add(a)

	def contains(self, var: str) -> bool:
		return (var in self.edges) and (var not in self.removed)

	def remove(self, var: str) -> None:
		self.removed.add(var)

	def unremove(self, var: str) -> None:
		self.removed.remove(var)

	def get_degree(self, var: str) -> int:
		n = 0
		for neighbour in self.edges[var]:
			if neighbour not in self.removed:
				n += 1

		return n

	def get_neighbours(self, var: str) -> Set[str]:
		if var in self.removed:
			return set()

		ret: Set[str] = set()
		for neigh in self.edges[var]:
			if neigh not in self.removed:
				ret.add(neigh)

		return ret



	def get_remaining_nodes(self) -> Set[str]:
		return set(filter(lambda x: x not in self.removed, self.edges))

	def get_simplifiable_node(self, max_degree: int, exclude: Set[str] = set()) -> Optional[str]:
		for var in sorted(self.edges):
			if (var not in self.removed) and (var not in exclude) and (self.get_degree(var) < max_degree):
				return var

		return None
