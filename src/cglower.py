#!/usr/bin/env python

from __future__ import annotations
from typing import *
from copy import *

from . import ir3
from . import cgpseudo
from .util import Location, TCException, CGException, StringView, print_warning, escape_string


def lower_const_value(value: ir3.Value, ctr: List[int]) -> Tuple[List[ir3.Stmt], List[ir3.VarDecl], ir3.Value]:
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
def lower_expr(expr: ir3.Expr, ctr: List[int]) -> Tuple[List[ir3.Stmt], List[ir3.VarDecl], ir3.Expr]:
	if isinstance(expr, ir3.BinaryOp):
		s1, vrs1, v1 = lower_const_value(expr.lhs, ctr)
		s2, vrs2, v2 = lower_const_value(expr.rhs, ctr)
		if len(s1) == 0 and len(s2) == 0:
			return [], [], expr
		return [ *s1, *s2 ], [ *vrs1, *vrs2 ], ir3.BinaryOp(expr.loc, v1, expr.op, v2)

	elif isinstance(expr, ir3.UnaryOp):
		ss, vr, v = lower_const_value(expr.expr, ctr)
		if len(ss) == 0:
			return [], [], expr
		return ss, vr, ir3.UnaryOp(expr.loc, expr.op, v)

	elif isinstance(expr, ir3.ValueExpr):
		ss, vr, v = lower_const_value(expr.value, ctr)
		return ss, vr, ir3.ValueExpr(expr.loc, v)

	elif isinstance(expr, ir3.FnCallExpr):
		ss = []
		vs = []
		vrs = []
		for arg in expr.call.args:
			s, vr, v = lower_const_value(arg, ctr)
			ss.extend(s)
			vrs.extend(vr)
			vs.append(v)

		if len(ss) == 0:
			return [], [], expr

		return ss, vrs, ir3.FnCallExpr(expr.loc, ir3.FnCall(expr.loc, expr.call.name, vs))

	else:
		return [], [], expr


def lower_stmt(stmt: ir3.Stmt, ctr: List[int]) -> Tuple[List[ir3.Stmt], List[ir3.VarDecl]]:
	if isinstance(stmt, ir3.AssignOp):
		ss, vr, e = lower_expr(stmt.rhs, ctr)
		if len(ss) == 0:
			return [ stmt ], []
		return [ *ss, ir3.AssignOp(stmt.loc, stmt.lhs, e) ], vr

	elif isinstance(stmt, ir3.AssignDotOp):
		ss, vr, e = lower_expr(stmt.rhs, ctr)
		if len(ss) == 0:
			return [ stmt ], []
		return [ *ss, ir3.AssignDotOp(stmt.loc, stmt.lhs1, stmt.lhs2, e) ], vr

	elif isinstance(stmt, ir3.PrintLnCall):
		ss, vr, v = lower_const_value(stmt.value, ctr)
		if len(ss) == 0:
			return [ stmt ], []
		return [ *ss, ir3.PrintLnCall(stmt.loc, v) ], vr

	elif isinstance(stmt, ir3.FnCallStmt):
		ss = []
		vs = []
		vrs = []
		for arg in stmt.call.args:
			s, vr, v = lower_const_value(arg, ctr)
			ss.extend(s)
			vs.append(v)
			vrs.extend(vr)

		if len(ss) == 0:
			return [ stmt ], []

		return [ *ss, ir3.FnCallStmt(stmt.loc, ir3.FnCall(stmt.loc, stmt.call.name, vs)) ], vrs

	elif isinstance(stmt, ir3.ReturnStmt):
		if stmt.value is None:
			return [ stmt ], []
		ss, vr, v = lower_const_value(stmt.value, ctr)
		if len(ss) == 0:
			return [ stmt ], []
		return [ *ss, ir3.ReturnStmt(stmt.loc, v) ], vr

	elif isinstance(stmt, ir3.CondBranch):
		if not isinstance(stmt.cond, ir3.RelOp):
			return [ stmt ], []

		ss1, vr1, v1 = lower_const_value(stmt.cond.lhs, ctr)
		ss2, vr2, v2 = lower_const_value(stmt.cond.rhs, ctr)
		if len(ss1) == 0 and len(ss2) == 0:
			return [ stmt ], []
		rel = ir3.RelOp(stmt.cond.loc, stmt.cond.lhs, stmt.cond.op, stmt.cond.rhs)
		return [ *ss1, *ss2, ir3.CondBranch(stmt.loc, rel, stmt.label) ], [ *vr1, *vr2 ]

	else:
		return [ stmt ], []


def lower_function(func: ir3.FuncDefn) -> None:

	# first, lower all statements.
	const_nums = [0]
	func.blocks[0].stmts.insert(0, cgpseudo.DummyStmt(func.loc))

	for b in func.blocks:
		backup = copy(b.stmts)
		b.stmts = []
		for s in backup:
			ss, vrs = lower_stmt(s, const_nums)
			func.vars.extend(vrs)

			b.stmts.extend(ss)
			const_nums[0] += 1


def renumber_stmts(func: ir3.FuncDefn) -> List[ir3.Stmt]:

	counter = 0
	all_stmts: List[ir3.Stmt] = []

	for b in func.blocks:
		for s in b.stmts:
			s.id = counter
			counter += 1
			all_stmts.append(s)

	return all_stmts
