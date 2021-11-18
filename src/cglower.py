#!/usr/bin/env python

from __future__ import annotations
from typing import *
from copy import *

from . import ir3
from . import cgpseudo
from .util import Location, TCException, CGException, StringView, print_warning, escape_string



def split_constant_multiply(lhs: ir3.Value, mult: int, ctr: List[int]) -> Tuple[List[ir3.Stmt], List[ir3.VarDecl], ir3.Expr]:
	# there is a whole field about optimising this, apparently.
	# "Single Constant Multiplication". unfortunately i'm too 3head to understand any of the papers,
	# so this is a 3head solution.

	# it's far easier to do this...
	ss, vs, mul = lower_const_value(ir3.ConstantInt(lhs.loc, mult), ctr, force_int = True)
	return ss, vs, ir3.BinaryOp(lhs.loc, lhs, '*', mul)


def lower_const_value(value: ir3.Value, ctr: List[int], force_int: bool = False) -> Tuple[List[ir3.Stmt], List[ir3.VarDecl], ir3.Value]:
	stm: ir3.Stmt
	vname = f"_c{ctr[0]}"
	ctr[0] += 1

	if isinstance(value, ir3.ConstantInt):
		# we know "for sure" that any value between -256 and +256 (inclusive) can be encoded as
		# an immediate operand
		if (not force_int) and (-256 <= value.value <= 256):
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
		# special case '*' here. we cannot multiply by a constant on arm, because it sucks.
		if (expr.op == '*') and (isinstance(expr.lhs, ir3.ConstantInt) or isinstance(expr.rhs, ir3.ConstantInt)):
			if isinstance(expr.lhs, ir3.ConstantInt):
				return split_constant_multiply(expr.rhs, expr.lhs.value, ctr)
			elif isinstance(expr.rhs, ir3.ConstantInt):
				return split_constant_multiply(expr.lhs, expr.rhs.value, ctr)


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
		# the rhs must first be saved into a temporary, because we don't want to (re)introduce
		# scratch registers (to place the result of the rhs expr). then we lower this into
		# a separate "store" instruction.
		tmp = ir3.VarDecl(stmt.loc, f"_g{ctr[0] + 1}", "Int")

		ss, vr, e = lower_expr(stmt.rhs, ctr)
		ss.extend([
			ir3.AssignOp(stmt.loc, tmp.name, e),
			cgpseudo.StoreField(stmt.loc, stmt.lhs1, stmt.lhs2, tmp.name, stmt.type)
		])

		ctr[0] += 1
		vr.append(tmp)

		return ss, vr

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

		# we also lower this to only have a var or const in the condition.
		ss1, vr1, v1 = lower_const_value(stmt.cond.lhs, ctr)
		ss2, vr2, v2 = lower_const_value(stmt.cond.rhs, ctr)
		rel = ir3.BinaryOp(stmt.cond.loc, stmt.cond.lhs, stmt.cond.op, stmt.cond.rhs)
		tmp_name = f"_b{ctr[0]}"
		vr3 = [ ir3.VarDecl(stmt.loc, tmp_name, "Bool") ]
		ss3 = [ ir3.AssignOp(stmt.loc, tmp_name, rel) ]
		ctr[0] += 1

		return [ *ss1, *ss2, *ss3, ir3.CondBranch(stmt.loc, ir3.VarRef(stmt.loc, tmp_name), stmt.label) ], [ *vr1, *vr2, *vr3 ]

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
