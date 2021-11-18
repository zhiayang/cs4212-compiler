#!/usr/bin/env python

from __future__ import annotations
from typing import *
from copy import *

from . import ir3
from . import iropt
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

	elif isinstance(stmt, cgpseudo.StoreField):
		return set(), set([stmt.ptr, stmt.rhs])

	else:
		return set(), set()



# returns (ins, outs, defs, uses)
def analyse(func: ir3.FuncDefn, all_stmts: List[ir3.Stmt]) -> Tuple[List[Set[str]], List[Set[str]], \
	List[Set[str]], List[Set[str]]]:

	predecessors = iropt.compute_predecessors(func)
	successors = iropt.compute_successors(func)

	ins: List[Set[str]]  = list(map(lambda _: set(), range(0, len(all_stmts))))
	outs: List[Set[str]] = list(map(lambda _: set(), range(0, len(all_stmts))))
	queue: List[int] = list(range(0, len(all_stmts)))

	defs: List[Set[str]] = list(map(lambda s: get_defs_and_uses(s)[0], all_stmts))
	uses: List[Set[str]] = list(map(lambda s: get_defs_and_uses(s)[1], all_stmts))

	# furthermore, we consider the first statement to define all locals (incl. temporaries) and arguments.
	defs[0].update(map(lambda v: v.name, func.vars))
	defs[0].update(map(lambda v: v.name, func.params))

	while len(queue) > 0:
		n = queue.pop(0)
		stmt = all_stmts[n]

		old_in = copy(ins[n])

		tmp: Set[str] = set()       # stupidest language ever designed
		outs[n] = tmp.union(*map(lambda succ: ins[succ], successors[n]))
		ins[n]  = uses[n].union(outs[n] - defs[n])

		if old_in != ins[n] and n in predecessors:
			queue.extend(predecessors[n])

	return (ins, outs, defs, uses)
