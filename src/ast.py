#/usr/bin/env python

from __future__ import annotations
from typing import *
from abc import ABC, abstractmethod

class Expr(ABC):
	@abstractmethod
	def __str__(self) -> str: ...

class Stmt(ABC):
	@abstractmethod
	def __str__(self) -> str: ...

class FuncCall:
	def __init__(self, name: str, args: List[Expr]) -> None:
		self.name: str = name
		self.args: List[Expr] = args

	def __str__(self) -> str:
		return f"{self.name}({','.join(map(str, self.args))})"

class BinaryOp(Expr):
	def __init__(self, left: Expr, right: Expr, op: str) -> None:
		self.lhs: Expr = left
		self.rhs: Expr = right
		self.op: str = op

	def __str__(self) -> str:
		return f"({self.lhs} {self.op} {self.rhs})"

class UnaryOp(Expr):
	def __init__(self, expr: Expr, op: str) -> None:
		self.expr: Expr = expr
		self.op: str = op

	def __str__(self) -> str:
		return f"{self.op}{self.expr}"

class VarRef(Expr):
	def __init__(self, name: str) -> None:
		self.name: str = name

	def __str__(self) -> str:
		return f"{self.name}"

class FuncCallExpr(FuncCall, Expr):
	def __init__(self, name: str, args: List[Expr]) -> None:
		super().__init__(name, args)

	def __str__(self) -> str:
		return super().__str__()

class NewExpr(Expr):
	def __init__(self, class_name: str) -> None:
		self.class_name: str = class_name

	def __str__(self) -> str:
		return f"new {self.class_name}()"

class StringLit(Expr):
	def __init__(self, value: str) -> None:
		self.value: str = value

	# TODO: this should re-escape the string literal
	def __str__(self) -> str:
		return f"\"{self.value}\""

class BooleanLit(Expr):
	def __init__(self, value: bool) -> None:
		self.value: bool = value

	def __str__(self) -> str:
		return f"{'true' if self.value else 'false'}"

class IntegerLit(Expr):
	def __init__(self, value: int) -> None:
		self.value: int = value

	def __str__(self) -> str:
		return f"{self.value}"

class NullLit(Expr):
	def __init__(self) -> None:
		pass

	def __str__(self) -> str:
		return "null"

class ThisLit(Expr):
	def __init__(self) -> None:
		pass

	def __str__(self) -> str:
		return "this"

class DotOp(Expr):
	def __init__(self, lhs: Expr, rhs: Expr) -> None:
		self.lhs: Expr = lhs
		self.rhs: Expr = rhs

	def __str__(self) -> str:
		return f"{self.lhs}.{self.rhs}"

class FuncCallStmt(FuncCall, Stmt):
	def __init__(self, name: str, args: List[Expr]) -> None:
		super().__init__(name, args)

	def __str__(self) -> str:
		return f"{super().__str__()};"

class ReadLnCall(Stmt):
	def __init__(self, var: str) -> None:
		self.var: str = var

	def __str__(self) -> str:
		return f"readln({self.var});"

class PrintLnCall(Stmt):
	def __init__(self, expr: Expr) -> None:
		self.expr: Expr = expr

	def __str__(self) -> str:
		return f"println({self.expr});"

class ReturnStmt(Stmt):
	def __init__(self, value: Optional[Expr]) -> None:
		self.value: Optional[Expr] = value

	def __str__(self) -> str:
		return f"return{'' if self.value is None else (' ' + str(self.value))};"

class AssignStmt(Stmt):
	def __init__(self, lhs: Expr, rhs: Expr) -> None:
		self.lhs: Expr = lhs
		self.rhs: Expr = rhs

	def __str__(self) -> str:
		return f"{self.lhs} = {self.rhs};"

class VarDecl:
	def __init__(self, name: str, type: str) -> None:
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
	def __init__(self, condition: Expr, true_case: Block, else_case: Block) -> None:
		self.condition: Expr = condition
		self.true_case: Block = true_case
		self.else_case: Block = else_case

	def __str__(self) -> str:
		return f"if({self.condition})\n{self.true_case}\nelse\n{self.else_case}"

class WhileLoop(Stmt):
	def __init__(self, condition: Expr, body: Block) -> None:
		self.condition: Expr = condition
		self.body: Block = body

	def __str__(self) -> str:
		return f"while({self.condition})\n{self.body}"

class MethodDefn:
	def __init__(self, name: str, parent: ClassDefn, args: List[VarDecl], return_type: str, vars: List[VarDecl], body: Block) -> None:
		self.name: str = name
		self.parent: ClassDefn = parent
		self.args: List[VarDecl] = args
		self.return_type: str = return_type
		self.vars: List[VarDecl] = vars
		self.body: Block = body

	def __str__(self) -> str:
		return f"{self.return_type} {self.name}({','.join(map(lambda x: str(x)[:-1], self.args))})" \
			+ "\n{\n" + "\n".join(map(lambda x: "    " + str(x), self.vars)) \
			+ "\n" + "\n".join(map(lambda x: "    " + str(x), self.body.stmts)) \
			+ "\n}"

class ClassDefn:
	def __init__(self, name: str, fields: List[VarDecl], methods: List[MethodDefn]) -> None:
		self.name: str = name
		self.fields: List[VarDecl] = fields
		self.methods: List[MethodDefn] = methods

	def __str__(self) -> str:
		return f"class {self.name}\n" + "{\n" \
			+ "\n".join(map(lambda x: "    " + str(x), self.fields)) + "\n" \
			+ "\n".join(map(lambda x: "    " + str(x), self.methods)) + "\n}"

class Program:
	def __init__(self, classes: List[ClassDefn]) -> None:
		assert len(classes) > 0
		self.classes: List[ClassDefn] = classes

	def __str__(self) -> str:
		return "\n\n".join(map(str, self.classes))
