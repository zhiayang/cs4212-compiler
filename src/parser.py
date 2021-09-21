#!/usr/bin/env python

from .lexer import *
from .util import StringView
from .util.file import Location

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


# def parse_program():

