#/usr/bin/env python

from __future__ import annotations
from typing import *
from copy import *

# we are all simps on this blessed day
# this just does constant folding and other stuff.
from . import ast


def simplify_expr(expr: ast.Expr) -> ast.Expr:
	if isinstance(expr, ast.FuncCall):
		for i, arg in enumerate(expr.args):
			expr.args[i] = simplify_expr(arg)

	elif isinstance(expr, ast.BinaryOp):
		bi: ast.BinaryOp = expr
		lhs = simplify_expr(bi.lhs)
		rhs = simplify_expr(bi.rhs)

		if isinstance(lhs, ast.StringLit) and isinstance(rhs, ast.StringLit):
			if bi.op == "+":
				return ast.StringLit(bi.loc, lhs.value + rhs.value)

		elif isinstance(lhs, ast.BooleanLit) and isinstance(rhs, ast.BooleanLit):
			if bi.op == "&&":
				return ast.BooleanLit(bi.loc, lhs.value and rhs.value)
			elif bi.op == "||":
				return ast.BooleanLit(bi.loc, lhs.value or rhs.value)

		elif isinstance(lhs, ast.IntegerLit) and isinstance(rhs, ast.IntegerLit):
			if bi.op == "+":    return ast.IntegerLit(bi.loc, lhs.value + rhs.value)
			elif bi.op == "-":  return ast.IntegerLit(bi.loc, lhs.value - rhs.value)
			elif bi.op == "*":  return ast.IntegerLit(bi.loc, lhs.value * rhs.value)
			elif bi.op == "/":  return ast.IntegerLit(bi.loc, lhs.value // rhs.value)

			elif bi.op == "<":  return ast.BooleanLit(bi.loc, lhs.value < rhs.value)
			elif bi.op == ">":  return ast.BooleanLit(bi.loc, lhs.value > rhs.value)
			elif bi.op == ">=":  return ast.BooleanLit(bi.loc, lhs.value >= rhs.value)
			elif bi.op == "<=":  return ast.BooleanLit(bi.loc, lhs.value <= rhs.value)
			elif bi.op == "==":  return ast.BooleanLit(bi.loc, lhs.value == rhs.value)
			elif bi.op == "!=":  return ast.BooleanLit(bi.loc, lhs.value != rhs.value)

		return ast.BinaryOp(bi.loc, lhs, rhs, bi.op)

	elif isinstance(expr, ast.UnaryOp):
		un: ast.UnaryOp = expr
		un.expr = simplify_expr(un.expr)

		# double whatever is gone
		if isinstance(un.expr, ast.UnaryOp) and un.expr.op == expr.op:
			return un.expr.expr

		# let's just make negative literals, why not.
		elif isinstance(un.expr, ast.IntegerLit) and un.op == "-":
			return ast.IntegerLit(un.expr.loc, -1 * un.expr.value)

		elif isinstance(un.expr, ast.BooleanLit) and un.op == "!":
			return ast.BooleanLit(un.expr.loc, not un.expr.value)

	# we can actually just get rid of ParenExpr at this level
	elif isinstance(expr, ast.ParenExpr):
		return simplify_expr(expr.expr)

	return expr

def simplify_stmt(stmt: ast.Stmt) -> ast.Stmt:
	if isinstance(stmt, ast.PrintLnCall):
		stmt.expr = simplify_expr(stmt.expr)

	elif isinstance(stmt, ast.ExprStmt):
		stmt.expr = simplify_expr(stmt.expr)

	elif isinstance(stmt, ast.ReturnStmt):
		if stmt.value is not None:
			stmt.value = simplify_expr(stmt.value)

	elif isinstance(stmt, ast.AssignStmt):
		stmt.rhs = simplify_expr(stmt.rhs)

	elif isinstance(stmt, ast.IfStmt):
		stmt.condition = simplify_expr(stmt.condition)
		stmt.true_case = simplify_block(stmt.true_case)
		stmt.else_case = simplify_block(stmt.else_case)

	elif isinstance(stmt, ast.WhileLoop):
		stmt.condition = simplify_expr(stmt.condition)
		stmt.body = simplify_block(stmt.body)

	return stmt

def simplify_block(block: ast.Block) -> ast.Block:
	for i, stmt in enumerate(block.stmts):
		block.stmts[i] = simplify_stmt(stmt)

	return block

def simplify_program(prog: ast.Program) -> ast.Program:
	for cls in prog.classes:
		for mth in cls.methods:
			mth.body = simplify_block(mth.body)

	return prog
