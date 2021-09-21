#!/usr/bin/env python

from __future__ import annotations
from typing import *

from . import ast

from .lexer import *
from .util import StringView

class ParserState:
	def __init__(self, filename: str, s: StringView):
		self.stream: StringView = s
		self.loc: Location = Location(filename, 0, 0)

	def peek(self) -> Token:
		tok, _, _ = read_token(self.stream, self.loc)
		return tok

	def next(self) -> Token:
		tok, rest, l = read_token(self.stream, self.loc)
		self.stream = rest
		self.loc = l
		return tok

	def empty(self) -> bool:
		return self.stream.empty()













def parse_class(state: ParserState) -> ast.ClassDefn:
	pass


def parse_program(state: ParserState) -> ast.Program:
	classes: List[ast.ClassDefn] = []
	while not state.empty():
		classes.append(parse_class(state))

	return ast.Program(classes)

