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
		return f"{self.lhs} = {self.rhs};"
