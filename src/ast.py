#/usr/bin/env python

from __future__ import annotations
from typing import *
from abc import ABC, abstractmethod

from .util import Location, escape_string

def indent_lines(x: str) -> str:
	return "\n".join(map(lambda s: "    " + s, x.split("\n")))

class Expr(ABC):
	def __init__(self, loc: Location) -> None:
		self.loc: Location = loc

	@abstractmethod
	def __str__(self) -> str: ...

class Stmt(ABC):
	def __init__(self, loc: Location) -> None:
		self.loc: Location = loc

	@abstractmethod
	def __str__(self) -> str: ...


# since expressions are not explicitly statements, we need a way to represent
# things that *could be* expressions and *also* statements -- namely function calls.
class ExprStmt(Stmt):
	def __init__(self, expr: Expr) -> None:
		super().__init__(expr.loc)
		self.expr: Expr = expr

	def __str__(self) -> str:
		return f"{self.expr};"

class FuncCall(Expr):
	def __init__(self, loc: Location, func: Expr, args: List[Expr]) -> None:
		super().__init__(loc)
		self.func: Expr = func
		self.args: List[Expr] = args

	def __str__(self) -> str:
		return f"{self.func}({', '.join(map(str, self.args))})"

class BinaryOp(Expr):
	def __init__(self, loc: Location, left: Expr, right: Expr, op: str) -> None:
		super().__init__(loc)
		self.lhs: Expr = left
		self.rhs: Expr = right
		self.op: str = op

	def __str__(self) -> str:
		return f"({self.lhs} {self.op} {self.rhs})"

class UnaryOp(Expr):
	def __init__(self, loc: Location, expr: Expr, op: str) -> None:
		super().__init__(loc)
		self.expr: Expr = expr
		self.op: str = op

	def __str__(self) -> str:
		return f"{self.op}{self.expr}"

class VarRef(Expr):
	def __init__(self, loc: Location, name: str) -> None:
		super().__init__(loc)
		self.name: str = name

	def __str__(self) -> str:
		return f"{self.name}"

class NewExpr(Expr):
	def __init__(self, loc: Location, class_name: str) -> None:
		super().__init__(loc)
		self.class_name: str = class_name

	def __str__(self) -> str:
		return f"new {self.class_name}()"

class StringLit(Expr):
	def __init__(self, loc: Location, value: str) -> None:
		super().__init__(loc)
		self.value: str = value

	# TODO: this should re-escape the string literal
	def __str__(self) -> str:
		return f"\"{escape_string(self.value)}\""

class BooleanLit(Expr):
	def __init__(self, loc: Location, value: bool) -> None:
		super().__init__(loc)
		self.value: bool = value

	def __str__(self) -> str:
		return f"{'true' if self.value else 'false'}"

class IntegerLit(Expr):
	def __init__(self, loc: Location, value: int) -> None:
		super().__init__(loc)
		self.value: int = value

	def __str__(self) -> str:
		return f"{self.value}"

class NullLit(Expr):
	def __init__(self, loc: Location) -> None:
		super().__init__(loc)

	def __str__(self) -> str:
		return "null"

class ThisLit(Expr):
	def __init__(self, loc: Location) -> None:
		super().__init__(loc)

	def __str__(self) -> str:
		return "this"

class ParenExpr(Expr):
	def __init__(self, expr: Expr) -> None:
		super().__init__(expr.loc)
		self.expr: Expr = expr

	def __str__(self) -> str:
		# don't insert useless parens, since BinaryOp already surrounds itself with ()
		if isinstance(self.expr, BinaryOp):
			return f"{self.expr}"
		else:
			return f"({self.expr})"

class DotOp(Expr):
	def __init__(self, loc: Location, lhs: Expr, rhs: Expr) -> None:
		super().__init__(loc)
		self.lhs: Expr = lhs
		self.rhs: Expr = rhs

	def __str__(self) -> str:
		return f"{self.lhs}.{self.rhs}"

class ReadLnCall(Stmt):
	def __init__(self, loc: Location, var: str) -> None:
		super().__init__(loc)
		self.var: str = var

	def __str__(self) -> str:
		return f"readln({self.var});"

class PrintLnCall(Stmt):
	def __init__(self, loc: Location, expr: Expr) -> None:
		super().__init__(loc)
		self.expr: Expr = expr

	def __str__(self) -> str:
		return f"println({self.expr});"

class ReturnStmt(Stmt):
	def __init__(self, loc: Location, value: Optional[Expr]) -> None:
		super().__init__(loc)
		self.value: Optional[Expr] = value

	def __str__(self) -> str:
		return f"return{'' if self.value is None else (' ' + str(self.value))};"

class AssignStmt(Stmt):
	def __init__(self, loc: Location, lhs: Expr, rhs: Expr) -> None:
		super().__init__(loc)
		self.lhs: Expr = lhs
		self.rhs: Expr = rhs

	def __str__(self) -> str:
		return f"{self.lhs} = {self.rhs};"

class VarDecl:
	def __init__(self, loc: Location, name: str, type: str) -> None:
		self.loc: Location = loc
		self.name: str = name
		self.type: str = type

	def __str__(self) -> str:
		return f"{self.type} {self.name};"

class Block:
	def __init__(self, stmts: List[Stmt]) -> None:
		self.stmts: List[Stmt] = stmts

	def __str__(self) -> str:
		return "{\n" + "\n".join(map(lambda x: "    " + str(x), self.stmts)) + "\n}"

class IfStmt(Stmt):
	def __init__(self, loc: Location, condition: Expr, true_case: Block, else_case: Block) -> None:
		super().__init__(loc)
		self.condition: Expr = condition
		self.true_case: Block = true_case
		self.else_case: Block = else_case

	def __str__(self) -> str:
		return f"if({self.condition})\n{indent_lines(str(self.true_case))}\n    else\n{indent_lines(str(self.else_case))}"

class WhileLoop(Stmt):
	def __init__(self, loc: Location, condition: Expr, body: Block) -> None:
		super().__init__(loc)
		self.condition: Expr = condition
		self.body: Block = body

	def __str__(self) -> str:
		return f"while({self.condition})\n{indent_lines(str(self.body))}"

class MethodDefn:
	def __init__(self, loc: Location, name: str, parent: ClassDefn, args: List[VarDecl], return_type: str,
				 vars: List[VarDecl], body: Block) -> None:
		self.loc: Location = loc
		self.name: str = name
		self.parent: ClassDefn = parent
		self.args: List[VarDecl] = args
		self.return_type: str = return_type
		self.vars: List[VarDecl] = vars
		self.body: Block = body

	def __str__(self) -> str:
		return f"{self.return_type} {self.name}({', '.join(map(lambda x: str(x)[:-1], self.args))})" \
			+ "\n    {\n" + "\n".join(map(lambda x: "    " + indent_lines(str(x)), self.vars)) \
			+ ("\n" if len(self.vars) > 0 else "") \
			+ "\n".join(map(lambda x: "    " + indent_lines(str(x)), self.body.stmts)) \
			+ "\n    }"

class ClassDefn:
	def __init__(self, loc: Location, name: str, fields: List[VarDecl], methods: List[MethodDefn]) -> None:
		self.loc: Location = loc
		self.name: str = name
		self.fields: List[VarDecl] = fields
		self.methods: List[MethodDefn] = methods

	def __str__(self) -> str:
		return f"class {self.name}\n" + "{\n" \
			+ "\n".join(map(lambda x: "    " + str(x), self.fields)) \
			+ ("\n" if len(self.fields) > 0 else "") \
			+ "\n".join(map(lambda x: "    " + str(x), self.methods)) + "\n}"

class Program:
	def __init__(self, classes: List[ClassDefn]) -> None:
		assert len(classes) > 0
		self.classes: List[ClassDefn] = classes

	def __str__(self) -> str:
		return "\n\n".join(map(str, self.classes))
