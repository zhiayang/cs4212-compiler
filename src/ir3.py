#/usr/bin/env python

from __future__ import annotations
from typing import *
from abc import ABC, abstractmethod

from .util import Location, escape_string

def indent_lines(x: str) -> str:
	return "\n".join(map(lambda s: "    " + s, x.split("\n")))

class Value(ABC):
	def __init__(self, loc: Location) -> None:
		self.loc: Location = loc

	@abstractmethod
	def __str__(self) -> str: ...

class ConstantInt(Value):
	def __init__(self, loc: Location, value: int) -> None:
		super().__init__(loc)
		self.value: int = value

	def __str__(self) -> str:
		return str(self.value)

class ConstantString(Value):
	def __init__(self, loc: Location, value: str) -> None:
		super().__init__(loc)
		self.value: str = value

	def __str__(self) -> str:
		return f"\"{self.value}\""

class ConstantBool(Value):
	def __init__(self, loc: Location, value: bool) -> None:
		super().__init__(loc)
		self.value: bool = value

	def __str__(self) -> str:
		return f"{'true' if self.value else 'false'}"

class ConstantNull(Value):
	def __init__(self, loc: Location) -> None:
		super().__init__(loc)

	def __str__(self) -> str:
		return "null"

class VarRef(Value):
	def __init__(self, loc: Location, name: str) -> None:
		super().__init__(loc)
		self.name: str = name

	def __str__(self) -> str:
		return self.name

class VarDecl:
	def __init__(self, loc: Location, name: str, type: str) -> None:
		self.loc: Location = loc
		self.name: str = name
		self.type: str = type

	def __str__(self) -> str:
		return f"{self.type} {self.name}"




class Stmt(ABC):
	def __init__(self, loc: Location) -> None:
		self.loc: Location = loc

	@abstractmethod
	def __str__(self) -> str: ...

class Expr(ABC):
	def __init__(self, loc: Location) -> None:
		self.loc: Location = loc

	@abstractmethod
	def __str__(self) -> str: ...


class BinaryOp(Expr):
	def __init__(self, loc: Location, lhs: Value, op: str, rhs: Value) -> None:
		super().__init__(loc)
		self.lhs: Value = lhs
		self.rhs: Value = rhs
		self.op: str = op

	def __str__(self) -> str:
		return f"{self.lhs} {self.op} {self.rhs}"

class UnaryOp(Expr):
	def __init__(self, loc: Location, op: str, expr: Value) -> None:
		super().__init__(loc)
		self.expr: Value = expr
		self.op: str = op

	def __str__(self) -> str:
		return f"{self.op}{self.expr}"

class DotOp(Expr):
	def __init__(self, loc: Location, lhs: str, rhs: str) -> None:
		super().__init__(loc)
		self.lhs: str = lhs
		self.rhs: str = rhs

	def __str__(self) -> str:
		return f"{self.lhs}.{self.rhs}"

class ValueExpr(Expr):
	def __init__(self, loc: Location, value: Value) -> None:
		super().__init__(loc)
		self.value: Value = value

	def __str__(self) -> str:
		return f"{self.value}"

class NewOp(Expr):
	def __init__(self, loc: Location, cls: str) -> None:
		super().__init__(loc)
		self.cls: str = cls

	def __str__(self) -> str:
		return f"new {self.cls}()"

class FnCall:
	def __init__(self, loc: Location, name: str, args: List[Value]) -> None:
		self.loc: Location = loc
		self.name: str = name
		self.args: List[Value] = args

	def __str__(self) -> str:
		return f"{self.name}({', '.join(map(str, self.args))})"

class FnCallExpr(Expr):
	def __init__(self, loc: Location, call: FnCall) -> None:
		super().__init__(loc)
		self.call: FnCall = call

	def __str__(self) -> str:
		return str(self.call)





class Label(Stmt):
	def __init__(self, loc: Location, name: str) -> None:
		super().__init__(loc)
		self.name: str = name

	def __str__(self) -> str:
		return f"Label {self.name}:"

class FnCallStmt(Stmt):
	def __init__(self, loc: Location, call: FnCall) -> None:
		super().__init__(loc)
		self.call: FnCall = call

	def __str__(self) -> str:
		return f"{self.call};"

class AssignOp(Stmt):
	def __init__(self, loc: Location, lhs: str, rhs: Expr) -> None:
		super().__init__(loc)
		self.lhs: str = lhs
		self.rhs: Expr = rhs

	def __str__(self) -> str:
		return f"{self.lhs} = {self.rhs};"

class AssignDotOp(Stmt):
	def __init__(self, loc: Location, lhs1: str, lhs2: str, rhs: Expr) -> None:
		super().__init__(loc)
		self.lhs1: str = lhs1
		self.lhs2: str = lhs2
		self.rhs: Expr = rhs

	def __str__(self) -> str:
		return f"{self.lhs1}.{self.lhs2} = {self.rhs};"

class ReturnStmt(Stmt):
	def __init__(self, loc: Location, value: Optional[Value]) -> None:
		super().__init__(loc)
		self.value: Optional[Value] = value

	def __str__(self) -> str:
		return f"return{'' if self.value is None else (' ' + str(self.value))};"

class ReadLnCall(Stmt):
	def __init__(self, loc: Location, name: str) -> None:
		super().__init__(loc)
		self.name: str = name

	def __str__(self) -> str:
		return f"readln({self.name});"

class PrintLnCall(Stmt):
	def __init__(self, loc: Location, value: Value) -> None:
		super().__init__(loc)
		self.value: Value = value

	def __str__(self) -> str:
		return f"println({self.value});"

class Branch(Stmt):
	def __init__(self, loc: Location, label: str) -> None:
		super().__init__(loc)
		self.label: str = label

	def __str__(self) -> str:
		return f"goto {self.label};"


class RelOp:
	def __init__(self, loc: Location, lhs: Value, op: str, rhs: Value) -> None:
		self.loc: Location = loc
		self.lhs: Value = lhs
		self.rhs: Value = rhs
		self.op: str = op

	def __str__(self) -> str:
		return f"{self.lhs} {self.op} {self.rhs}"

class CondBranch(Stmt):
	def __init__(self, loc: Location, cond: Union[Value, RelOp], label: str) -> None:
		super().__init__(loc)
		self.label: str = label
		self.cond: Union[Value, RelOp] = cond

	def __str__(self) -> str:
		return f"if ({self.cond}) goto {self.label};"




class ClassDefn:
	def __init__(self, loc: Location, name: str, fields: List[VarDecl]) -> None:
		self.loc: Location = loc
		self.name: str = name
		self.fields: List[VarDecl] = fields

	def __str__(self) -> str:
		return f"class {self.name}\n" + "{\n" \
			+ "\n".join(map(lambda x: f"    {x};", self.fields)) + "\n}"

class FuncDefn:
	def __init__(self, loc: Location, name: str, parent: str, params: List[VarDecl], return_type: str,
				 vars: List[VarDecl], body: List[Stmt]) -> None:
		self.loc: Location = loc
		self.name: str = name
		self.parent: str = parent
		self.params: List[VarDecl] = params
		self.return_type: str = return_type
		self.vars: List[VarDecl] = vars
		self.body: List[Stmt] = body

	def __str__(self) -> str:
		tmp1 = ", ".join(map(str, self.params))
		tmp2 = map(lambda x: f"{x};", self.vars)

		return f"{self.return_type} {self.name}({tmp1})" \
			+ "\n{\n" + "\n".join(map(lambda x: indent_lines(x), tmp2)) \
			+ ("\n" if len(self.vars) > 0 else "") \
			+ "\n".join(map(lambda x: indent_lines(str(x)), self.body)) \
			+ "\n}"

class Program:
	def __init__(self, classes: List[ClassDefn], funcs: List[FuncDefn]) -> None:
		self.classes: List[ClassDefn] = classes
		self.funcs: List[FuncDefn] = funcs

	def __str__(self) -> str:
		return "\n\n".join(map(str, self.classes)) + "\n\n" + "\n\n".join(map(str, self.funcs))

