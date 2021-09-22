#!/usr/bin/env python

from __future__ import annotations
from typing import *

import sys
import os

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

	def advancing_line(self) -> Location:
		return Location(self.filename, self.line + 1, 0)

	def __str__(self) -> str:
		return f"{self.filename}:{self.line + 1}:{self.column + 1}"

def colourise(msg: str, colour: str) -> str:
	if sys.stdout.isatty():
		return f"\x1b[{colour}{msg}\x1b[0m"
	else:
		return msg


TAB_WIDTH = 4

class ParseException(Exception):
	def __init__(self, loc: Location, msg: str) -> None:
		self.loc: Location = loc
		self.msg: str = msg

	def throw(self) -> NoReturn:
		print(f"{self.loc}: {colourise('error:', '1;31m')} {colourise(self.msg, '1m')}")

		# print the gutter
		gutter_width = 4 + len(str(1 + self.loc.line))

		# we have the filename, so just read the file again
		offending_code: str = open(self.loc.filename, "rb").read().splitlines()[self.loc.line].decode("utf-8")
		offending_code = offending_code.replace('\t', ' ' * TAB_WIDTH)

		trimmed_code = "    " + offending_code.lstrip()

		arrow = "    " + (' ' * (self.loc.column - len(offending_code) - len(trimmed_code))) + '^'

		print(f"{' ' * (gutter_width - 2)}| ")
		print(f" {1 + self.loc.line} | {trimmed_code}")
		print(f"{' ' * (gutter_width - 2)}| {colourise(arrow, '1;31m')}")
		sys.exit(1)

