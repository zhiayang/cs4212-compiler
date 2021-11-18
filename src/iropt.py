#/usr/bin/env python

from __future__ import annotations
from typing import *
from copy import *
from functools import reduce

from . import ast
from . import ir3
from . import simp
from . import cgpseudo

from . import util


def remove_unreachable_blocks(func: ir3.FuncDefn) -> bool:
	block_names: Dict[str, ir3.BasicBlock] = {}
	for block in func.blocks:
		block_names[block.name] = block

	def check_reachability(block: ir3.BasicBlock, seen: Set[str]) -> Set[str]:
		ret: Set[str] = set()
		ret.add(block.name)
		if block.name in seen:
			return ret

		# again, we need some workarounds because ir3's branch is *not* a basic-block style jump
		for stmt in block.stmts:
			if isinstance(stmt, ir3.Branch):
				ret = ret.union(check_reachability(block_names[stmt.label], seen.union(ret)))

			elif isinstance(stmt, ir3.CondBranch):
				ret = ret.union(check_reachability(block_names[stmt.label], seen.union(ret)))

		return ret


	# keep removing things until nothing changes.
	visited: Set[str] = set()

	removed_blocks = []
	while True:
		new_visited = check_reachability(func.blocks[0], set())
		if new_visited == visited:
			break

		visited = new_visited

		# remove any blocks that are not reachable
		unreachables = set(func.blocks).difference(map(lambda x: block_names[x], visited))
		for unr in unreachables:
			func.blocks.remove(unr)
			removed_blocks.append(unr)
			print(f"removing {unr.name}")

	for rem in removed_blocks:
		for blk in func.blocks:
			blk.predecessors.discard(rem)

	log_opt(func, "unreachable block", len(removed_blocks))
	return len(removed_blocks) > 0


def remove_double_jumps(func: ir3.FuncDefn) -> bool:
	# while we're here, prune any blocks that contain just a single unconditional branch.
	# eg. if we have a: { ... jmp b; }, b: { jmp c; }, c: { ... }, then we can replace it
	# with simply a: { ... jmp c; }, c: { ... } and yeet b from existence.

	num_removed = 0
	# do this weird slice thing to make a copy so we can yeet elements while iterating.
	for blk in func.blocks[:]:
		if len(blk.stmts) == 1 and isinstance(blk.stmts[0], ir3.Branch):
			target = blk.stmts[0].label

			# replace all predecessors to jump to the new target. note (again) that, because
			# ir3 doesn't have proper `if {cond} goto {label} else goto {label}` forms, we need
			# to actually check the last *TWO* statements in a block.

			for pred in blk.predecessors:
				for j in pred.stmts:
					if isinstance(j, ir3.Branch) and j.label == blk.name:
						j.label = target
					elif isinstance(j, ir3.CondBranch) and j.label == blk.name:
						j.label = target

			num_removed += 1

	# note that we only eliminate the double jump. the unreachable-block pruning actually
	# removes the "middle" block, since it is now unreachable.

	log_opt(func, "double-jump", num_removed)
	return num_removed > 0


def remove_redundant_temporaries(func: ir3.FuncDefn) -> bool:
	# we often generate slightly scuffed IR like this:
	# _t1 = a + b;
	# m = _t1;
	# this optimisation pass simply checks if a variable (_t1 in this case)
	# is only used once, and that only use is on the next line (in the same block) to assign to someone else.
	# if so, it eliminates the redundant _t1, and does `m = a + b` directly.

	# first, figure out which block each statement is in
	parent_blocks: Dict[int, str] = dict()
	block_names: Dict[str, ir3.BasicBlock] = dict()
	for blk in func.blocks:
		block_names[blk.name] = blk
		for s in blk.stmts:
			parent_blocks[s.id] = blk.name

	num_removed = 0
	for temp in filter(lambda x: x.name.startswith("_"), func.vars):
		assigns = get_var_assigns(func, temp.name)
		# can only be assigned once. anyway for temporary variables we essentially generate SSA,
		# so we shouldn't encounter this case... by right.
		if len(assigns) != 1:
			continue

		ass = assigns[0]
		if not isinstance(ass, ir3.AssignOp):
			continue

		next_id = ass.id + 1

		# not in the same block; i don't want to do flow analysis, so just ignore this.
		if (next_id not in parent_blocks) or (parent_blocks[next_id] != parent_blocks[ass.id]):
			continue

		# get the block...
		block = block_names[parent_blocks[ass.id]]
		next_stmt = next(filter(lambda s: s.id == next_id, block.stmts))

		if isinstance(next_stmt, ir3.AssignOp) or isinstance(next_stmt, ir3.AssignDotOp):
			if isinstance(next_stmt.rhs, ir3.ValueExpr) and isinstance(next_stmt.rhs.value, ir3.VarRef):
				if next_stmt.rhs.value.name == temp.name:
					# ok, we are clear to eliminate this guy. another pass will
					# remove unused variables, so we don't need to check it here
					# (and anyway removing statements will mess up the numbering)
					assert isinstance(ass, ir3.AssignOp)
					next_stmt.rhs = ass.rhs
					num_removed += 1

	log_opt(func, "redundant assignment", num_removed)
	return num_removed > 0


def remove_unused_variables(func: ir3.FuncDefn) -> bool:
	# this is not limited to removing temporary variables. of course,
	# we can't eliminate dotop assigns, but that's fine; otherwise, we
	# can eliminate params, user-defined locals, and temporaries.

	# we also must note to extract any side effects from the rhs of the assign.

	parent_blocks: Dict[int, ir3.BasicBlock] = dict()
	for blk in func.blocks:
		for s in blk.stmts:
			parent_blocks[s.id] = blk

	num_removed = 0
	for var in func.vars[:]:
		uses = get_var_uses(func, var.name)
		if len(uses) == 0:
			assigns = get_var_assigns(func, var.name)
			for ass in assigns:
				assert isinstance(ass, ir3.AssignOp) or isinstance(ass, ir3.AssignDotOp)

				# check if the rhs has side effects
				side_effect = get_side_effects(ass.rhs)
				if side_effect is not None:
					# if it does, replace the assign with the side effect. the variable
					# still gets yeeted, but any side effects used to assign it (ie. function calls)
					# are still executed.
					parent_blocks[ass.id].stmts[parent_blocks[ass.id].stmts.index(ass)] = side_effect

				else:
					parent_blocks[ass.id].stmts.remove(ass)

			func.vars.remove(var)
			num_removed += 1

	log_opt(func, "unused variable", num_removed)
	return num_removed > 0


def eliminate_common_subexpressions(func: ir3.FuncDefn, all_stmts: List[ir3.Stmt], all_exprs: List[ir3.Expr]) -> bool:
	# perform forward flow analysis.
	ins, outs, gens, kills = forward_dataflow(func, all_stmts, int, all_exprs,
		get_stmt_gen_exprs, get_stmt_kill_exprs)

	# gens is a map of stmt -> gen-ed expr
	# we want to invert it. to get expr -> variable name
	# we know that only assignments generate expressions.

	expr_generators: Dict[int, str] = dict()
	for n, gs in enumerate(gens):
		# there isn't a statement that generates more than 1 expression
		assert len(gs) <= 1

		if len(gs) == 1:
			expr_id = list(gs)[0]

			# all generators should be an assign
			stmt = all_stmts[n]
			assert isinstance(stmt, ir3.AssignOp)

			# each expression is only generated by one statement
			assert expr_id not in expr_generators
			expr_generators[expr_id] = stmt.lhs



	# there should be no expression being generated from 2 statements.

	num_removed = 0
	for i, stmt in enumerate(all_stmts):
		# these are the expressions that reach this statement
		in_exprs = ins[i]

		# for this statement, check if it uses one of the in_exprs. this is
		# only possible if the statement is an assign (nobody else has expressions)
		if isinstance(stmt, ir3.AssignOp) or isinstance(stmt, ir3.AssignDotOp):
			# check if the expression has side effects (is a 'new' or a function call).
			# if so, we cannot eliminate it. note that we consider 'new' here, because
			# we obviously need unique 'new's for each use of it. (it needs to be... new) haHAA

			if isinstance(stmt.rhs, ir3.FnCallExpr) or isinstance(stmt.rhs, ir3.NewOp):
				continue

			# ok, now see if any expression that reaches us is equivalent:
			for in_expr_id in in_exprs:
				if (all_exprs[in_expr_id] == stmt.rhs) and (in_expr_id != stmt.rhs.id):
					# match -- replace it with the variable that made it;
					stmt.rhs = ir3.ValueExpr(stmt.rhs.loc, ir3.VarRef(stmt.rhs.loc, expr_generators[in_expr_id]))
					num_removed += 1

	log_opt(func, "common subexpression", num_removed)
	return num_removed > 0





def optimise(func: ir3.FuncDefn):

	passes = 0
	while True:
		passes += 1

		all_stmts = renumber_statements(func)
		all_exprs = renumber_expressions(all_stmts)

		# compute_available_expressions(func, all_stmts)

		# these things might remove statements, which screws up the numbering.
		# it's safer to just restart it (and renumber the statements) when any
		# of the optimisations makes a change.

		if remove_unreachable_blocks(func):     continue
		if remove_double_jumps(func):           continue
		if remove_redundant_temporaries(func):  continue
		if remove_unused_variables(func):       continue

		if eliminate_common_subexpressions(func, all_stmts, all_exprs):
			continue

		# finished
		break

	util.log(f"opt({func.name}): completed in {passes} pass{'' if passes == 1 else 'es'}")




# helpers

T = TypeVar("T")
K = TypeVar("K")
def forward_dataflow(func: ir3.FuncDefn, all_stmts: List[ir3.Stmt], set_types: Type[T], all_things: List[K],
	get_gens: Callable[[ir3.Stmt, List[K]], Set[T]],
	get_kills: Callable[[ir3.Stmt, List[K]], Set[T]]) -> Tuple[List[Set[T]], List[Set[T]], List[Set[T]], List[Set[T]]]:

	# forward dataflow analysis. determines the in/out for expressions.
	# we do this on a statement basis. similar algorithm to liveness in cgliveness.py.

	successors = compute_successors(func)
	predecessors = compute_predecessors(func)

	# ins are empty by default, but outs are the gens of each statement by default.

	ins: List[Set[T]]  = list(map(lambda _: set(), all_stmts))
	outs: List[Set[T]] = list(map(lambda _: set(), all_stmts))

	gens: List[Set[T]] = list(map(lambda s: get_gens(s, all_things), all_stmts))
	kills: List[Set[T]] = list(map(lambda s: get_kills(s, all_things), all_stmts))

	queue: List[int] = list(range(0, len(all_stmts)))
	while len(queue) > 0:
		n = queue.pop(0)
		stmt = all_stmts[n]

		old_out = copy(outs[n])

		# dumb. python is dumb
		if len(predecessors[n]) == 0:
			ins[n] = set()
		else:
			ins[n]  = reduce(set.intersection, map(lambda pred: outs[pred], predecessors[n]))

		outs[n] = gens[n].union(ins[n] - kills[n])
		if old_out != outs[n] and n in successors:
			queue.extend(successors[n])

	return ins, outs, gens, kills


def get_stmt_gen_exprs(stmt: ir3.Stmt, _: List[ir3.Expr]) -> Set[int]:
	# a statement only "generates" an expression when there is an expression on its rhs.
	# we do not want to consider dotops to "generate" their expressions (since it would
	# be too expensive to load from memory versus just doing arithmetic), so we are left
	# with only normal assigns. further, only consider temporaries, since they are in SSA.

	# since normal vars are not constrained to SSA, we cannot just assign (x = b) since b
	# might have been redefined somewhere in the middle. with SSA, we can be sure that is
	# not the case.
	if isinstance(stmt, ir3.AssignOp) and stmt.lhs.startswith("_"):
		return set([ stmt.rhs.id ])
	else:
		return set()


def get_stmt_kill_exprs(stmt: ir3.Stmt, all_exprs: List[ir3.Expr]) -> Set[int]:
	stmt_defs = get_statement_defs(stmt)

	# an expression is "killed" by this statement if the statement defines
	# some value that the expression uses.
	def is_killed(expr: ir3.Expr) -> bool:
		return len(get_expr_uses(expr).intersection(stmt_defs)) > 0

	# a statement can kill any expression, so we need them all
	return set(map(lambda x: x.id, filter(is_killed, all_exprs)))





def compute_predecessors(func: ir3.FuncDefn) -> Dict[int, Set[int]]:
	predecessors: Dict[int, Set[int]] = dict()
	for b in func.blocks:
		first_id = b.stmts[0].id

		# for the first stmt in the block, its preds are the set of all branches to it.
		# for subsequent stmts, its pred is just the previous statement.
		predecessors[first_id] = set()
		for pred in b.predecessors:
			for j in pred.stmts[-2:]:
				if isinstance(j, ir3.Branch) and j.label == b.name:
					predecessors[first_id].add(j.id)
				elif isinstance(j, ir3.CondBranch) and j.label == b.name:
					predecessors[first_id].add(j.id)

		for k in range(1, len(b.stmts)):
			x = b.stmts[k].id
			predecessors[x] = set([x - 1])

	return predecessors


def compute_successors(func: ir3.FuncDefn) -> Dict[int, Set[int]]:
	labels: Dict[str, int] = { b.name: b.stmts[0].id for b in func.blocks }
	successors: Dict[int, Set[int]] = dict()

	for b in func.blocks:
		first_id = b.stmts[0].id
		for i, stmt in enumerate(b.stmts):
			if isinstance(stmt, ir3.Branch):
				successors[stmt.id] = set([ labels[stmt.label] ])

			elif isinstance(stmt, ir3.CondBranch):
				successors[stmt.id] = set([ labels[stmt.label] ])
				if i + 1 < len(b.stmts):
					successors[stmt.id].add(first_id + i + 1)

			elif i + 1 < len(b.stmts):
				successors[stmt.id] = set([first_id + i + 1])

			else:
				assert isinstance(stmt, ir3.Branch) or isinstance(stmt, ir3.ReturnStmt)
				successors[stmt.id] = set()

	return successors


def get_statement_defs(stmt: ir3.Stmt) -> Set[str]:
	if isinstance(stmt, ir3.ReadLnCall):
		return set([ stmt.name ])

	elif isinstance(stmt, ir3.AssignOp):
		return set([ stmt.lhs ])

	elif isinstance(stmt, cgpseudo.AssignConstInt):
		return set([ stmt.lhs ])

	elif isinstance(stmt, cgpseudo.AssignConstString):
		return set([ stmt.lhs ])

	elif isinstance(stmt, cgpseudo.RestoreVariable):
		return set([ stmt.var ])

	elif isinstance(stmt, cgpseudo.PhiNode):
		return set([ stmt.lhs ])

	else:
		return set()


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


def get_statement_uses(stmt: ir3.Stmt) -> Set[str]:
	if isinstance(stmt, ir3.FnCallStmt):
		tmp: Set[str] = set()           # stupidest language ever designed
		return tmp.union(*map(lambda a: get_value_uses(a), stmt.call.args))

	elif isinstance(stmt, ir3.ReturnStmt):
		return get_value_uses(stmt.value) if stmt.value is not None else set()

	elif isinstance(stmt, ir3.PrintLnCall):
		return get_value_uses(stmt.value)

	elif isinstance(stmt, ir3.AssignOp):
		return get_expr_uses(stmt.rhs)

	elif isinstance(stmt, ir3.CondBranch):
		if isinstance(stmt.cond, ir3.Value):
			return get_value_uses(stmt.cond)
		else:
			uses: Set[str] = set()
			return uses.union(get_value_uses(stmt.cond.lhs), get_value_uses(stmt.cond.rhs))

	elif isinstance(stmt, cgpseudo.SpillVariable):
		return set([ stmt.var ])

	elif isinstance(stmt, cgpseudo.StoreField):
		return set([stmt.ptr, stmt.rhs])

	elif isinstance(stmt, cgpseudo.PhiNode):
		return set(map(lambda x: x[0], stmt.values))

	else:
		return set()


def renumber_statements(func: ir3.FuncDefn) -> List[ir3.Stmt]:
	counter = 0
	all_stmts: List[ir3.Stmt] = []

	for b in func.blocks:
		for s in b.stmts:
			s.id = counter
			counter += 1
			all_stmts.append(s)

	return all_stmts


def renumber_expressions(all_stmts: List[ir3.Stmt]) -> List[ir3.Expr]:
	counter = 0
	all_exprs: List[ir3.Expr] = []
	for stmt in all_stmts:
		# nothing else has expressions, kekw.
		if isinstance(stmt, ir3.AssignOp) or isinstance(stmt, ir3.AssignDotOp):
			stmt.rhs.id = counter
			all_exprs.append(stmt.rhs)

		counter += 1

	return all_exprs





def log_opt(func: ir3.FuncDefn, kind: str, num: int):
	if num > 0:
		util.log(f"opt({func.name}): removed {num} {kind}{'' if num == 1 else 's'}")


def get_var_uses(func: ir3.FuncDefn, var: str) -> List[ir3.Stmt]:
	ret: List[ir3.Stmt] = []
	for blk in func.blocks:
		ret.extend(filter(lambda x: is_var_used_in_stmt(x, var), blk.stmts))

	return ret


def get_var_assigns(func: ir3.FuncDefn, var: str) -> List[ir3.Stmt]:
	ret: List[ir3.Stmt] = []
	for blk in func.blocks:
		ret.extend(filter(lambda x: (isinstance(x, ir3.AssignOp) or isinstance(x, cgpseudo.PhiNode)) and x.lhs == var,
			blk.stmts))

	return ret


def get_side_effects(expr: ir3.Expr) -> Optional[ir3.Stmt]:
	# actually, the only expressions with side effects in IR3 are call expressions.
	# unary and binary ops only take a Value, which is either a constant or a variable.
	if isinstance(expr, ir3.FnCallExpr):
		return ir3.FnCallStmt(expr.loc, expr.call)

	return None


def is_var_used_in_value(value: ir3.Value, var: str) -> bool:
	return isinstance(value, ir3.VarRef) and value.name == var

def is_var_used_in_expr(expr: ir3.Expr, var: str) -> bool:
	if isinstance(expr, ir3.BinaryOp):
		return is_var_used_in_value(expr.lhs, var) or is_var_used_in_value(expr.rhs, var)

	elif isinstance(expr, ir3.UnaryOp):
		return is_var_used_in_value(expr.expr, var)

	elif isinstance(expr, ir3.DotOp):
		return expr.lhs == var

	elif isinstance(expr, ir3.ValueExpr):
		return is_var_used_in_value(expr.value, var)

	elif isinstance(expr, ir3.FnCallExpr):
		return len(list(filter(None, map(lambda v: is_var_used_in_value(v, var), expr.call.args)))) > 0

	else:
		return False


def is_var_used_in_stmt(stmt: ir3.Stmt, var: str) -> bool:
	if isinstance(stmt, ir3.FnCallStmt):
		return len(list(filter(None, map(lambda v: is_var_used_in_value(v, var), stmt.call.args)))) > 0

	elif isinstance(stmt, ir3.AssignOp) or isinstance(stmt, ir3.AssignDotOp):
		return is_var_used_in_expr(stmt.rhs, var)

	elif isinstance(stmt, ir3.ReturnStmt):
		return is_var_used_in_value(stmt.value, var) if stmt.value is not None else False

	elif isinstance(stmt, ir3.ReadLnCall):
		return stmt.name == var

	elif isinstance(stmt, ir3.PrintLnCall):
		return is_var_used_in_value(stmt.value, var)

	elif isinstance(stmt, ir3.CondBranch):
		if isinstance(stmt.cond, ir3.RelOp):
			return is_var_used_in_value(stmt.cond.lhs, var) or is_var_used_in_value(stmt.cond.rhs, var)
		else:
			return is_var_used_in_value(stmt.cond, var)

	elif isinstance(stmt, cgpseudo.PhiNode):
		return var in map(lambda x: x[0], stmt.values)

	else:
		return False