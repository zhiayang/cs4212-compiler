#!/usr/bin/env python

from __future__ import annotations
from typing import *
from copy import *

from . import ir3
from . import cgpseudo
from .util import Location, TCException, CGException, StringView, print_warning, escape_string

import math

def expand_constant_value(value: ir3.Value, ctr: List[int]) -> Tuple[List[ir3.Stmt], List[ir3.VarDecl], ir3.Value]:
	stm: ir3.Stmt
	vname = f"_c{ctr[0]}"
	ctr[0] += 1

	if isinstance(value, ir3.ConstantInt):
		# we know "for sure" that any value between -256 and +256 (inclusive) can be encoded as
		# an immediate operand
		if -256 <= value.value <= 256:
			return [], [], value

		var = ir3.VarDecl(value.loc, vname, "Int")
		stm = cgpseudo.AssignConstInt(value.loc, vname, value.value)

		return [ stm ], [ var ], ir3.VarRef(value.loc, vname)

	elif isinstance(value, ir3.ConstantString):
		# this always needs expanding.
		var = ir3.VarDecl(value.loc, vname, "String")
		stm = cgpseudo.AssignConstString(value.loc, vname, value.value)

		return [ stm ], [ var ], ir3.VarRef(value.loc, vname)

	else:
		return [], [], value


# for constants that cannot fit in an immediate (ie. strings, integers out of range),
def expand_constants_in_expr(expr: ir3.Expr, ctr: List[int]) -> Tuple[List[ir3.Stmt], List[ir3.VarDecl], ir3.Expr]:
	if isinstance(expr, ir3.BinaryOp):
		s1, vrs1, v1 = expand_constant_value(expr.lhs, ctr)
		s2, vrs2, v2 = expand_constant_value(expr.rhs, ctr)
		if len(s1) == 0 and len(s2) == 0:
			return [], [], expr
		return [ *s1, *s2 ], [ *vrs1, *vrs2 ], ir3.BinaryOp(expr.loc, v1, expr.op, v2)

	elif isinstance(expr, ir3.UnaryOp):
		ss, vr, v = expand_constant_value(expr.expr, ctr)
		if len(ss) == 0:
			return [], [], expr
		return ss, vr, ir3.UnaryOp(expr.loc, expr.op, v)

	elif isinstance(expr, ir3.ValueExpr):
		ss, vr, v = expand_constant_value(expr.value, ctr)
		return ss, vr, ir3.ValueExpr(expr.loc, v)

	elif isinstance(expr, ir3.FnCallExpr):
		ss = []
		vs = []
		vrs = []
		for arg in expr.call.args:
			s, vr, v = expand_constant_value(arg, ctr)
			ss.extend(s)
			vrs.extend(vr)
			vs.append(v)

		if len(ss) == 0:
			return [], [], expr

		return ss, vrs, ir3.FnCallExpr(expr.loc, ir3.FnCall(expr.loc, expr.call.name, vs))

	else:
		return [], [], expr


def expand_constants_in_stmt(stmt: ir3.Stmt, ctr: List[int]) -> Tuple[List[ir3.Stmt], List[ir3.VarDecl]]:
	if isinstance(stmt, ir3.AssignOp):
		ss, vr, e = expand_constants_in_expr(stmt.rhs, ctr)
		if len(ss) == 0:
			return [ stmt ], []
		return [ *ss, ir3.AssignOp(stmt.loc, stmt.lhs, e) ], vr

	elif isinstance(stmt, ir3.AssignDotOp):
		ss, vr, e = expand_constants_in_expr(stmt.rhs, ctr)
		if len(ss) == 0:
			return [ stmt ], []
		return [ *ss, ir3.AssignDotOp(stmt.loc, stmt.lhs1, stmt.lhs2, e) ], vr

	elif isinstance(stmt, ir3.PrintLnCall):
		ss, vr, v = expand_constant_value(stmt.value, ctr)
		if len(ss) == 0:
			return [ stmt ], []
		return [ *ss, ir3.PrintLnCall(stmt.loc, v) ], vr

	elif isinstance(stmt, ir3.FnCallStmt):
		ss = []
		vs = []
		vrs = []
		for arg in stmt.call.args:
			s, vr, v = expand_constant_value(arg, ctr)
			ss.extend(s)
			vs.append(v)
			vrs.extend(vr)

		if len(ss) == 0:
			return [ stmt ], []

		return [ *ss, ir3.FnCallStmt(stmt.loc, ir3.FnCall(stmt.loc, stmt.call.name, vs)) ], vrs

	elif isinstance(stmt, ir3.ReturnStmt):
		if stmt.value is None:
			return [ stmt ], []
		ss, vr, v = expand_constant_value(stmt.value, ctr)
		if len(ss) == 0:
			return [ stmt ], []
		return [ *ss, ir3.ReturnStmt(stmt.loc, v) ], vr

	elif isinstance(stmt, ir3.CondBranch):
		if not isinstance(stmt.cond, ir3.RelOp):
			return [ stmt ], []

		ss1, vr1, v1 = expand_constant_value(stmt.cond.lhs, ctr)
		ss2, vr2, v2 = expand_constant_value(stmt.cond.rhs, ctr)
		if len(ss1) == 0 and len(ss2) == 0:
			return [ stmt ], []
		rel = ir3.RelOp(stmt.cond.loc, stmt.cond.lhs, stmt.cond.op, stmt.cond.rhs)
		return [ *ss1, *ss2, ir3.CondBranch(stmt.loc, rel, stmt.label) ], [ *vr1, *vr2 ]

	else:
		return [ stmt ], []


def renumber_statements(func: ir3.FuncDefn) -> List[ir3.Stmt]:

	# first, expand all statements.
	const_nums = [0]
	for b in func.blocks:
		backup = copy(b.stmts)
		b.stmts = []
		for i, s in enumerate(backup):
			ss, vrs = expand_constants_in_stmt(s, const_nums)
			func.vars.extend(vrs)

			b.stmts.extend(ss)
			const_nums[0] += 1

	all_stmts: List[ir3.Stmt] = []

	# then renumber them.
	counter = 0
	for b in func.blocks:
		for s in b.stmts:
			s.id = counter
			counter += 1
			all_stmts.append(s)

	return all_stmts


def get_defs_and_uses(stmt: ir3.Stmt) -> Tuple[Set[str], Set[str]]:

	def get_value_uses(val: ir3.Value) -> Set[str]:
		if isinstance(val, ir3.VarRef):
			return set([ val.name ])
		else:
			return set()

	def get_expr_uses(expr: ir3.Expr) -> Set[str]:
		if isinstance(expr, ir3.BinaryOp):
			return get_value_uses(expr.lhs).union(get_value_uses(expr.rhs))
		elif isinstance(expr, ir3.UnaryOp):
			return get_value_uses(expr.expr)
		elif isinstance(expr, ir3.DotOp):
			return set([expr.lhs])
		elif isinstance(expr, ir3.ValueExpr):
			return get_value_uses(expr.value)
		elif isinstance(expr, ir3.FnCallExpr):
			tmp: Set[str] = set()       # stupidest language ever designed
			return tmp.union(*map(lambda a: get_value_uses(a), expr.call.args))
		else:
			return set()

	if isinstance(stmt, ir3.FnCallStmt):
		# calls don't def anything
		tmp: Set[str] = set()           # stupidest language ever designed
		return (set(), tmp.union(*map(lambda a: get_value_uses(a), stmt.call.args)))
	elif isinstance(stmt, ir3.ReturnStmt):
		return (set(), get_value_uses(stmt.value) if stmt.value is not None else set())
	elif isinstance(stmt, ir3.ReadLnCall):
		return (set([ stmt.name ]), set())
	elif isinstance(stmt, ir3.PrintLnCall):
		return (set(), get_value_uses(stmt.value))
	elif isinstance(stmt, ir3.AssignOp):
		return (set([ stmt.lhs ]), get_expr_uses(stmt.rhs))
	elif isinstance(stmt, ir3.AssignDotOp):
		return (set([ stmt.lhs1 ]), get_expr_uses(stmt.rhs))
	elif isinstance(stmt, ir3.CondBranch):
		if isinstance(stmt.cond, ir3.Value):
			return (set(), get_value_uses(stmt.cond))
		else:
			uses: Set[str] = set()
			uses = uses.union(get_value_uses(stmt.cond.lhs), get_value_uses(stmt.cond.rhs))
			return (set(), uses)
	elif isinstance(stmt, cgpseudo.AssignConstInt):
		return (set([ stmt.lhs ]), set())
	elif isinstance(stmt, cgpseudo.AssignConstString):
		return (set([ stmt.lhs ]), set())
	else:
		return (set(), set())





# returns (ins, outs, defs, uses)
def analyse_liveness(func: ir3.FuncDefn, all_stmts: List[ir3.Stmt]) -> Tuple[List[Set[str]], List[Set[str]], \
	List[Set[str]], List[Set[str]]]:

	labels: Dict[str, int] = dict()
	predecessors: Dict[int, Set[int]] = dict()

	for b in func.blocks:
		labels[b.name] = b.stmts[0].id

		# for the first stmt in the block, its preds are the set of all branches to it.
		# for subsequent stmts, its pred is just the previous statement.
		predecessors[labels[b.name]] = set(map(lambda b: b.stmts[-1].id, b.predecessors))

		for k in range(1, len(b.stmts)):
			x = b.stmts[k].id
			predecessors[x] = set([x - 1])

	def get_successors(i: int) -> Set[int]:
		stmt = all_stmts[i]
		if isinstance(stmt, ir3.Branch):
			return set([ labels[stmt.label] ])

		elif isinstance(stmt, ir3.CondBranch):
			return set([ labels[stmt.label], i + 1 ])

		elif i + 1 < len(all_stmts):
			return set([i + 1])
		else:
			return set()

	ins: List[Set[str]]  = list(map(lambda _: set(), range(0, len(all_stmts))))
	outs: List[Set[str]] = list(map(lambda _: set(), range(0, len(all_stmts))))
	queue: List[int] = list(range(0, len(all_stmts)))

	defs: List[Set[str]] = list(map(lambda s: get_defs_and_uses(s)[0], all_stmts))
	uses: List[Set[str]] = list(map(lambda s: get_defs_and_uses(s)[1], all_stmts))

	# furthermore, we consider the first statement to define all locals (incl. temporaries) and arguments.
	defs[0].update(map(lambda v: v.name, func.vars))
	defs[0].update(map(lambda v: v.name, func.params))

	while len(queue) > 0:
		n = queue[0]
		stmt = all_stmts[n]
		queue = queue[1:]

		old_in = copy(ins[n])

		tmp: Set[str] = set()       # stupidest language ever designed
		outs[n] = tmp.union(*map(lambda succ: ins[succ], get_successors(n)))

		ins[n]  = uses[n].union(outs[n] - defs[n])

		# TODO: is this correct?
		if old_in != ins[n] and n in predecessors:
			queue.extend(predecessors[n])


	# for s in all_stmts:
	# 	print("{:02}:  {}".format(s.id, s))
	# 	print(f"  ins = {ins[s.id]}")



	return (ins, outs, defs, uses)


# func -> (assignments, spills, scratch, reg_live_ranges)
def allocate(func: ir3.FuncDefn) -> Tuple[Dict[str, str], Set[str], List[str], Dict[str, Set[int]]]:
	all_stmts = renumber_statements(func)
	ins, outs, defs, uses = analyse_liveness(func, all_stmts)


	# TODO: do we need to consider OUT for def? the idea here is that, if we have the following:
	# 0:  z = 69;
	# 1:  ...
	# 2:  k = z + 7;
	# 3:  ...
	# 4:  k = k + 1;
	#
	# without considering OUT, we have live(z) = { 1, 2 }, live(k) = { 3, 4 }
	# z and k here would *not* interfere. BUT, they actually don't -- nothing stops us
	# from assigning the same register to `k` and `z`.
	# if, in a subsequent line:
	#
	# 5:  ...
	# 6:  y = z + 1;
	#
	# then, live(z) = { 1, 2, 3, 4, 5, 6 }, which would interfere with live(k) = { 3, 4 } --
	# so it seems to suggest that we only need to consider IN.

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
	# we want to reverse it.
	var_uses: Dict[str, Set[int]] = dict()
	for n, us in enumerate(uses):
		for u in us:
			var_uses.setdefault(u, set()).add(n)


	# we must pre-colour the incoming arguments (which are not shadowed by locals) as a1-a4.
	pre_assigned: Dict[str, str] = dict()
	for i, param in enumerate(func.params[:4]):
		# only if it's not shadowed.
		if param.name not in func.vars:
			pre_assigned[param.name] = f"a{i + 1}"

	# we designate a3 and a4 as scratch registers. this lets us always have 2 registers
	# (guaranteed) into which we can load spilled operands.
	assigns, spills = colour_graph(graph, ["v1", "v2", "v3", "a1", "a2", "a3", "a4"],
		var_uses, pre_assigned)


	# the statements where the register is live. we just compute this from the assignment.
	reg_live_ranges: Dict[str, Set[int]] = dict()
	for var in assigns:
		reg = assigns[var]
		reg_live_ranges.setdefault(reg, set()).update(live_ranges[var])

	# print(f"assigns = {assigns}")
	# print(f"spills = {spills}")

	return assigns, spills, ["v4", "v5"], reg_live_ranges



def colour_graph(graph_: Graph, registers: List[str], uses: Dict[str, Set[int]], preassigned: Dict[str, str],
	to_spill: Set[str] = set()) -> Tuple[Dict[str, str], Set[str]]:

	graph = deepcopy(graph_)

	stack: List[str] = []
	preassigned_vars = set(preassigned.keys())

	while len(graph.get_remaining_nodes()) > 0:
		# we can't select preassigned vars to simplify.
		sel = graph.get_simplifiable_node(len(registers), exclude = preassigned_vars)

		if sel is not None:
			graph.remove(sel)
			stack.append(sel)
		else:
			# try again, but without excluding preassigned nodes. this moves them
			# as far back as possible so they are more likely to get their colour.
			sel = graph.get_simplifiable_node(len(registers), exclude = set())
			if sel is not None:
				graph.remove(sel)
				stack.append(sel)
				continue

			# choose a node to spill. we have a few heuristics to use:
			# 1. its degree, ie. how many other vars it interferes with
			#   spilling such a variable would make colouring easier later on
			# 2. how many times it is used
			#   spilling such a variable would be bad, because we need to touch memory more
			# 3. other stuff, but i can't be bothered.

			# so we just calculate a score here that is: num_uses / degree, and spill the smallest one.
			foo = list(map(lambda x: (x, len(uses[x]) / graph.get_degree(x)), graph.get_remaining_nodes()))
			foo.sort(key = lambda x: x[1])

			if len(foo) > 0:
				# now get the first one
				sel = foo[0][0]
				graph.remove(sel)
				stack.append(sel)
			else:
				raise CGException("failed to codegen: could not simplify interference graph")



	assignments: Dict[str, str] = dict()

	while len(stack) > 0:
		var = stack.pop(len(stack) - 1)
		graph.unremove(var)
		neighbours = graph.get_neighbours(var)

		used_regs = set(map(lambda x: assignments[x], neighbours))
		free_regs = list(filter(lambda x: x not in used_regs, registers))

		if len(free_regs) > 0:
			if var in preassigned and preassigned[var] in free_regs:
				assignments[var] = preassigned[var]
			else:
				assignments[var] = free_regs[0]
		else:
			print(f"spilling {var}")

			# oops, we *really* need to spill.
			new_graph = deepcopy(graph_)
			new_graph.remove(var)
			to_spill.add(var)
			return colour_graph(new_graph, registers, uses, preassigned, to_spill)


	return (assignments, to_spill)




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
		for var in self.edges:
			if (var not in self.removed) and (var not in exclude) and (self.get_degree(var) < max_degree):
				return var

		return None
