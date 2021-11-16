#!/usr/bin/env python

from __future__ import annotations
from typing import *
from copy import *

from . import ir3
from . import cglower
from . import cgpseudo
from .util import Location, TCException, CGException, StringView, print_warning, escape_string


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
		return set(), tmp.union(*map(lambda a: get_value_uses(a), stmt.call.args))

	elif isinstance(stmt, ir3.ReturnStmt):
		return set(), get_value_uses(stmt.value) if stmt.value is not None else set()

	elif isinstance(stmt, ir3.ReadLnCall):
		return set([ stmt.name ]), set()

	elif isinstance(stmt, ir3.PrintLnCall):
		return set(), get_value_uses(stmt.value)

	elif isinstance(stmt, ir3.AssignOp):
		return set([ stmt.lhs ]), get_expr_uses(stmt.rhs)

	elif isinstance(stmt, ir3.AssignDotOp):
		return set([ stmt.lhs1 ]), get_expr_uses(stmt.rhs)

	elif isinstance(stmt, ir3.CondBranch):
		if isinstance(stmt.cond, ir3.Value):
			return set(), get_value_uses(stmt.cond)
		else:
			uses: Set[str] = set()
			uses = uses.union(get_value_uses(stmt.cond.lhs), get_value_uses(stmt.cond.rhs))
			return set(), uses

	elif isinstance(stmt, cgpseudo.AssignConstInt):
		return set([ stmt.lhs ]), set()

	elif isinstance(stmt, cgpseudo.AssignConstString):
		return set([ stmt.lhs ]), set()

	elif isinstance(stmt, cgpseudo.SpillVariable):
		return set(), set([ stmt.var ])

	elif isinstance(stmt, cgpseudo.RestoreVariable):
		return set([ stmt.var ]), set()

	else:
		return set(), set()



# returns (ins, outs, defs, uses)
def analyse(func: ir3.FuncDefn, all_stmts: List[ir3.Stmt]) -> Tuple[List[Set[str]], List[Set[str]], \
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


	# 	print(f"-- {n} -- {stmt}")
	# 	print(f"  ins  = {ins[n]}")
	# 	print(f"  outs = {outs[n]}")
	# 	print(f"  preds = {predecessors[n]}")
	# 	print(f"  succs = {get_successors(n)}")
	# 	print(f"  queue = {queue}\n")


	# for s in all_stmts:
	# 	print("{:02}:  {}".format(s.id, s))
	# 	print(f"  ins = {ins[s.id]}")
	# 	print(f"  out = {outs[s.id]}")
	# 	print(f"  uses = {uses[s.id]}")
	# 	print(f"  preds = {predecessors[s.id]}")
	# 	print(f"  succs = {get_successors(s.id)}")
	# 	print("")



	return (ins, outs, defs, uses)
