#!/usr/bin/env python

from __future__ import annotations
from typing import *
from util import *

TAB_WIDTH = 4

class Token:
	def __init__(self, txt: StringView, ty: str, loc: Location):
		self.location: Location = loc
		self.text: StringView = txt
		self.type: str = ty

	def __str__(self) -> str:
		return f"Token({self.type}, '{self.text}')"

	def __eq__(self, other) -> bool:
		return (self.text == other.text) and (self.type == other.type)


def eat_whitespace(stream: StringView, loc: Location) -> Tuple[StringView, Location]:
	while True:
		if stream.starts_with_one_of(" \r"):
			stream.remove_prefix(1)
			loc.column += 1
		elif stream.starts_with("\t"):
			stream.remove_prefix(1)
			loc.column += TAB_WIDTH
		elif stream.starts_with("\n"):
			stream.remove_prefix(1)
			loc.line += 1
			loc.column = 0
		else:
			break

	return stream, loc

def read_string_literal(stream: StringView) -> Tuple[str, StringView, int]:
	assert stream.starts_with('"')
	value: str = ""

	def read_one_char(stream: StringView, index: int, msg: str) -> Tuple[int, str]:
		if index + 1 == stream.size():
			raise RuntimeError(f"unterminated string literal, {msg}")

		return (index + 1, chr(stream[index + 1]))

	idx: int = 1
	while idx < stream.size():
		if stream[idx] == ord("\\"):

			next: str
			idx, next = read_one_char(stream, idx, "unterminated '\\' escape")

			if next == "\\":
				value += "\\"
			elif next == "b":
				value += "\b"
			elif next == "n":
				value += "\n"
			elif next == "t":
				value += "\t"
			elif next == "r":
				value += "\r"

			elif ord('0') <= ord(next) <= ord('9'):
				# TODO: check whether this is really octal or not.
				# TODO: check whether this needs to have exactly 3 digits or not
				esc: int = ord(next) - ord('0')
				err_msg = "expected '\"'"
				idx, next = read_one_char(stream, idx, err_msg)

				if ord('0') <= ord(next) <= ord('9'):
					esc = esc * 10 + (ord(next) - ord('0'))
					idx, next = read_one_char(stream, idx, err_msg)

					if ord('0') <= ord(next) <= ord('9'):
						esc = esc * 10 + (ord(next) - ord('0'))
						idx, next = read_one_char(stream, idx, err_msg)

					elif next == '"':
						continue

				elif next == '"':
					continue

				# TODO: some input validation (eg. should we cap to 127?)
				value += chr(esc)
				continue

			elif next == 'x':
				# TODO: check whether this needs to have exactly 2 digits or not
				idx, next = read_one_char(stream, idx, "expected digits after '\\x'")
				esc = 0

				def is_hex_digit(d: str) -> Tuple[bool, int]:
					if ord('0') <= ord(d) <= ord('9'):
						return (True, ord('0'))
					elif ord('a') <= ord(d) <= ord('f'):
						return (True, ord('a'))
					elif ord('A') <= ord(d) <= ord('F'):
						return (True, ord('A'))
					else:
						return (False, 0)

				is_hex, sub = is_hex_digit(next)
				if not is_hex:
					raise RuntimeError(f"invalid hexadecimal digit '{next}' found in '\\x' escape")

				esc = ord(next) - sub
				idx, next = read_one_char(stream, idx, "expected digits after '\\x'")

				is_hex, sub = is_hex_digit(next)
				if is_hex:
					esc = 0x10 * esc + (ord(next) - sub)
					# read another one
					idx, next = read_one_char(stream, idx, "expected '\"'")

				value += chr(esc)
				continue

			elif next == "\r" or next == "\n":
				raise RuntimeError("unescaped newline in string literal")
			else:
				raise RuntimeError(f"invalid escape sequence '\\{next}' in string literal")

		elif stream[idx] == ord('"'):
			return value, stream.drop(idx + 1), idx + 1
		else:
			value += chr(stream[idx])

		idx += 1

	raise RuntimeError(f"unterminated string literal, expected '\"'")



# return (new_token, rest_of_the_stream)
def read_token(stream: StringView, loc: Location) -> Tuple[Token, StringView, Location]:
	stream, loc = eat_whitespace(stream, loc)

	if stream.empty():
		return Token(StringView(""), "EOF", loc), stream, loc

	if stream.starts_with("=="):
		return Token(stream.take_prefix(2), "==", loc), stream, loc.advancing(2)

	elif stream.starts_with("!="):
		return Token(stream.take_prefix(2), "!=", loc), stream, loc.advancing(2)

	elif stream.starts_with(">="):
		return Token(stream.take_prefix(2), ">=", loc), stream, loc.advancing(2)

	elif stream.starts_with("<="):
		return Token(stream.take_prefix(2), "<=", loc), stream, loc.advancing(2)

	elif stream.starts_with("&&"):
		return Token(stream.take_prefix(2), "&&", loc), stream, loc.advancing(2)

	elif stream.starts_with("||"):
		return Token(stream.take_prefix(2), "||", loc), stream, loc.advancing(2)

	elif stream.starts_with('"'):
		string, rest, n = read_string_literal(stream)
		return Token(StringView(string), "string_literal", loc), rest, loc.advancing(n)

	elif stream.starts_with_one_of(b"0123456789"):
		nums = stream.take_while(lambda x: ord('0') <= ord(x) <= ord('9'))
		return Token(nums, "num_literal", loc), stream.drop(nums.size()), loc.advancing(nums.size())

	elif stream.starts_with("//"):
		pass

	elif stream.starts_with("/*"):
		pass

	else:
		pass

	return Token(stream, "", loc), StringView(""), loc



test_input = r"""
== == != <=
||
&& "hello world"
"\x69 \n \bf4812 \\ ad \65b"
&&
"\x41" && "\x77" 69420 123 4812""
"""

if __name__ == "__main__":
	flag: bool = True
	loc: Location = Location("asdf", 0, 0)
	stream: StringView = StringView(test_input)

	while flag:
		tok: Token
		rest: StringView

		tok, rest, loc = read_token(stream, loc)
		stream = rest

		print(tok)
		if tok.type == "EOF":
			flag = False


