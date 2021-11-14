#!/usr/bin/env python

from __future__ import annotations
from typing import *

import sys
import os

def read_entire_file(filename: str) -> str:
	with open(filename, "rb") as f:
		return f.read().decode("utf-8")

def escape_string(s: str) -> str:
	out: str = ""
	for c in s:
		if 32 <= ord(c) <= 126:
			out += c
		elif c == '\n':
			out += "\\n"
		elif c == '\r':
			out += "\\r"
		elif c == '\t':
			out += "\\t"
		else:
			out += ("\\x%02x" % ord(c))

	return out


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

def print_context(loc: Location, colour: str) -> None:
	# print the gutter
	gutter_width = 4 + len(str(1 + loc.line))

	# we have the filename, so just read the file again
	file_lines = open(loc.filename, "rb").read().splitlines()
	if len(file_lines) > loc.line:
		offending_code: str = file_lines[loc.line].decode("utf-8")
		offending_code = offending_code.replace('\t', ' ' * TAB_WIDTH)
		trimmed_code = offending_code.lstrip()

		arrow = "    " + (' ' * (loc.column - (len(offending_code) - len(trimmed_code)))) + '^'

		print(f"{' ' * (gutter_width - 2)}|")
		print(     f" {1 + loc.line} |     {trimmed_code}")
		print(f"{' ' * (gutter_width - 2)}| {colourise(arrow, colour)}")


def print_error_msg(loc: Location, msg: str) -> None:
	print(f"{loc}: {colourise('error:', '1;31m')} {colourise(msg, '1m')}")
	print_context(loc, "1;31m")

def print_warning(loc: Location, msg: str) -> None:
	print(f"{loc}: {colourise('warning:', '1;35m')} {colourise(msg, '1m')}")
	print_context(loc, "1;35m")




class ParseException(Exception):
	def __init__(self, loc: Location, msg: str) -> None:
		self.loc: Location = loc
		self.msg: str = msg

	def throw(self) -> NoReturn:
		print_error_msg(self.loc, self.msg)
		sys.exit(1)

class TCException(Exception):
	def __init__(self, loc: Location, msg: str) -> None:
		self.loc: Location = loc
		self.msg: str = msg

	def throw(self) -> NoReturn:
		print_error_msg(self.loc, self.msg)
		sys.exit(1)

# this language sucks.
class CGException(Exception):
	def __init__(self, msg: str) -> None:
		self.msg: str = msg

	def throw(self) -> NoReturn:
		print(f"<unknown loc>: {colourise('error:', '1;31m')} {colourise(self.msg, '1m')}")
		sys.exit(1)
