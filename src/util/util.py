#!/usr/bin/env python

from __future__ import annotations
from typing import *

import sys

def read_entire_file(filename: str) -> str:
	with open(filename, "rb") as f:
		return f.read().decode("utf-8")

class Location:
	def __init__(self, filename: str, l: int, col: int):
		self.filename: str = filename
		self.column: int = col
		self.line: int = l

	def advancing(self, n: int) -> Location:
		return Location(self.filename, self.line, self.column + n)

	def __str__(self) -> str:
		return f"{self.filename}:{self.line + 1}:{self.column + 1}"

class ParseException(BaseException):
	def __init__(self, loc: Location, msg: str) -> None:
		self.loc: Location = loc
		self.msg: str = msg

		# actually, exit the program now.
		print(f"{self.loc}: {msg}")
		sys.exit(1)

