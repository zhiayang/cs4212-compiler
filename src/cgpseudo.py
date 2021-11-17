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

class GetElementPtr(ir3.Expr):
	def __init__(self, loc: Location, ptr: str, field: str) -> None:
		super().__init__(loc)
		self.ptr = ptr
		self.field = field

	def __str__(self) -> str:
		return f"getelementptr {self.ptr}, {self.field}"

class StoreField(ir3.Stmt):
	def __init__(self, loc: Location, ptr: str, value: ir3.Value, ty: str) -> None:
		super().__init__(loc)
		self.ptr = ptr
		self.value = value
		self.type = ty

	def __str__(self) -> str:
		return f"storefield: {self.type}, *{self.ptr} = {self.value};"

