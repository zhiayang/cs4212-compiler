#!/usr/bin/env python

from __future__ import annotations
from typing import *
from copy import *

from . import ir3

from .util import Location, TCException, CGException, StringView, print_warning, escape_string

class AssignConstInt(ir3.Stmt):
	def __init__(self, loc: Location, lhs: str, rhs: int) -> None:
		super().__init__(loc)
		self.lhs: str = lhs
		self.rhs: int = rhs

	def __str__(self) -> str:
		return f"{self.lhs} = {self.rhs};"


class AssignConstString(ir3.Stmt):
	def __init__(self, loc: Location, lhs: str, rhs: str) -> None:
		super().__init__(loc)
		self.lhs: str = lhs
		self.rhs: str = rhs

	def __str__(self) -> str:
		return f"{self.lhs} = \"{escape_string(self.rhs)}\";"


class DummyStmt(ir3.Stmt):
	def __init__(self, loc: Location) -> None:
		super().__init__(loc)

	def __str__(self) -> str:
		return f"dummy;"


class SpillVariable(ir3.Stmt):
	def __init__(self, loc: Location, var: str) -> None:
		super().__init__(loc)
		self.var: str = var

	def __str__(self) -> str:
		return f"spill {self.var};"

class RestoreVariable(ir3.Stmt):
	def __init__(self, loc: Location, var: str) -> None:
		super().__init__(loc)
		self.var: str = var

	def __str__(self) -> str:
		return f"restore {self.var};"

class StoreField(ir3.Stmt):
	def __init__(self, loc: Location, ptr: str, field: str, rhs_var: str, ty: str) -> None:
		super().__init__(loc)
		self.ptr = ptr
		self.field = field
		self.rhs = rhs_var
		self.type = ty

	def __str__(self) -> str:
		return f"storefield: {self.type}, *{self.ptr}.{self.field} = {self.rhs};"

# yes, i'm turning ir3 into SSA.
class PhiNode(ir3.Stmt):
	# values is a list of (var_name, assign_stmt)
	def __init__(self, loc: Location, var: str, values: List[Tuple[str, ir3.AssignOp]]) -> None:
		super().__init__(loc)
		self.lhs = var
		self.values = values

	def __str__(self) -> str:
		return f"{self.lhs} = phi {list(map(lambda x: x[0], self.values))};"

