#!/usr/bin/env python

from __future__ import annotations
from typing import *

from copy import copy
from .util import StringView, Location, ParseException, TAB_WIDTH

class Token:
	@overload
	def __init__(self, txt: StringView, ty: str, loc: Location): ...

	@overload
	def __init__(self, txt: str, ty: str, loc: Location): ...

	def __init__(self, txt: Union[StringView, str], ty: str, loc: Location):
		self.loc: Location = loc
		self.type: str = ty
		self.text: str

		if isinstance(txt, str):
			self.text = txt
		elif isinstance(txt, StringView):
			self.text = txt.string()
		else:
			raise TypeError(f"invalid type '{type(txt)}'")

	def __str__(self) -> str:
		return f"Token({self.type}, '{self.text}')"

	def __eq__(self, other: object) -> bool:
		return isinstance(other, Token) and (self.text == other.text) and (self.type == other.type)


def eat_whitespace(stream: StringView, loc: Location) -> Tuple[StringView, Location]:
	"""
	consumes whitespace from the stream.
	params:  input stream, current location
	returns: remaining stream, new location
	"""
	while True:
		if stream.starts_with_one_of(" \r"):
			stream.remove_prefix(1)
			loc = loc.advancing(1)
		elif stream.starts_with("\t"):
			stream.remove_prefix(1)
			loc = loc.advancing(TAB_WIDTH)
		elif stream.starts_with("\n"):
			stream.remove_prefix(1)
			loc = loc.advancing_line()
		else:
			break

	return stream, loc

def read_string_literal(stream: StringView, loc: Location) -> Tuple[str, StringView, int]:
	"""
	reads a string literal.
	params:  input stream
	returns: escaped string, remaining stream, bytes consumed
	"""
	assert stream.starts_with('"')
	value: str = ""

	def read_one_char(stream: StringView, index: int, msg: str) -> Tuple[int, str]:
		if index + 1 == stream.size():
			raise ParseException(loc.advancing(index), f"unterminated string literal, {msg}")

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
			elif next == "\"":
				value += "\""

			elif next.isdigit():
				for i in range(0, 3):
					if idx + i >= stream.size() or chr(stream[idx + i]) == '"':
						raise ParseException(loc.advancing(idx + i),
							f"premature end of string literal; decimal escapes must be 3 digits long")

					elif not (digit := chr(stream[idx + i])).isdigit():
						raise ParseException(loc.advancing(idx + i),
							f"invalid digit '{digit}' found in escape (which must be 3 digits long)")

				esc = int(stream[idx:(idx + 3)].string())
				idx += 3

				if esc > 127:
					raise ParseException(loc.advancing(idx), f"invalid ASCII escape; maximum value is 127, got {esc}")

				value += chr(esc)

				# we incremented idx manually, so skip
				continue

			elif next == 'x':
				for i in range(1, 3):
					if idx + i >= stream.size() or chr(stream[idx + i]) == '"':
						raise ParseException(loc.advancing(idx + i),
							f"premature end of string literal; hexadecimal escapes must be 2 digits long")

					digit = chr(stream[idx + i]).lower()
					if not (digit.isdigit() or ord('a') <= ord(digit) <= ord('f')):
						raise ParseException(loc.advancing(idx + i),
							f"invalid digit '{digit}' found in hexadecimal escape (which must be 2 digits long)")

				ch1 = ord(chr(stream[idx + 1]).lower())
				ch2 = ord(chr(stream[idx + 2]).lower())
				ch1 -= (ord('a') - 10) if chr(ch1).isalpha() else ord('0')
				ch2 -= (ord('a') - 10) if chr(ch2).isalpha() else ord('0')

				esc = (16 * ch1) + ch2
				idx += 3

				if esc > 127:
					raise ParseException(loc.advancing(idx), f"invalid ASCII escape; maximum value is 127, got {esc}")

				value += chr(esc)

				# we incremented idx manually, so skip
				continue

			elif next == "\r" or next == "\n":
				raise ParseException(loc.advancing(idx), "unescaped newline in string literal")

			else:
				raise ParseException(loc.advancing(idx), f"invalid escape sequence '\\{next}' in string literal")


		elif stream[idx] == ord('"'):
			return value, stream.drop(idx + 1), idx + 1
		else:
			value += chr(stream[idx])

		idx += 1

	raise ParseException(loc.advancing(idx), f"unterminated string literal, expected '\"'")


def read_identifier(stream: StringView) -> Tuple[str, StringView]:
	"""
	reads an identifier from the stream. note that the first character's validity is
	expected to be validated by the caller (since it can only be a letter)

	params:  input stream
	returns: identifier string, remaining stream
	"""
	num_chars: int = 0
	valid_chars: str = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789_"
	while stream.drop(num_chars).starts_with_one_of(valid_chars):
		num_chars += 1

	return stream.take(num_chars).string(), stream.drop(num_chars)





# return (new_token, rest_of_the_stream)
def read_token(stream: StringView, loc: Location) -> Tuple[Token, StringView, Location]:
	stream, loc = eat_whitespace(stream, loc)

	if stream.empty():
		return Token("", "EOF", loc), stream, loc

	if stream.starts_with("=="):
		return Token(stream.take_prefix(2), "EqualsTo", loc), stream, loc.advancing(2)

	elif stream.starts_with("!="):
		return Token(stream.take_prefix(2), "NotEqual", loc), stream, loc.advancing(2)

	elif stream.starts_with(">="):
		return Token(stream.take_prefix(2), "GreaterEqual", loc), stream, loc.advancing(2)

	elif stream.starts_with("<="):
		return Token(stream.take_prefix(2), "LessThanEqual", loc), stream, loc.advancing(2)

	elif stream.starts_with("&&"):
		return Token(stream.take_prefix(2), "LogicalAnd", loc), stream, loc.advancing(2)

	elif stream.starts_with("||"):
		return Token(stream.take_prefix(2), "LogicalOr", loc), stream, loc.advancing(2)

	elif stream.starts_with('"'):
		string, rest, n = read_string_literal(stream, loc)
		return Token(string, "StringLiteral", loc), rest, loc.advancing(n)

	elif stream.starts_with_one_of(b"0123456789"):
		nums = stream.take_while(lambda x: ord('0') <= ord(x) <= ord('9'))
		return Token(nums, "IntegerLiteral", loc), stream.drop(nums.size()), loc.advancing(nums.size())

	elif stream.starts_with("//"):
		line: StringView = stream.take_while(lambda x: x != "\n" and x != "\r")
		return Token(line, "Comment", loc), stream.drop(line.size()), loc.advancing(line.size())

	elif stream.starts_with("/*"):
		comment: StringView = stream.clone()

		stream.remove_prefix(2)
		nesting = 1

		new_loc: Location = loc
		while nesting > 0 and not stream.empty():
			if stream.starts_with("/*"):
				new_loc = new_loc.advancing(2)
				stream.remove_prefix(2)
				nesting += 1
			elif stream.starts_with("*/"):
				new_loc = new_loc.advancing(2)
				stream.remove_prefix(2)
				nesting -= 1
			else:
				if chr(stream[0]) in ['\r', '\n', '\t', ' ' ]:
					stream, new_loc = eat_whitespace(stream, new_loc)
				else:
					new_loc = new_loc.advancing(1)
					stream.remove_prefix(1)

		if nesting > 0:
			raise ParseException(loc, "unexpected end of input (expected '*/')")

		content: StringView = comment.drop_last(stream.size())
		return Token(content, "Comment", loc), stream, new_loc

	elif stream.starts_with("*/"):
		raise ParseException(loc, "illegal unpaired '*/'")

	elif stream.starts_with_one_of("abcdefghijklmnopqrstuvwxyz"):
		ident, rest = read_identifier(stream)

		tok_type: str = "Identifier"
		if ident == "if":           tok_type = "kw_if"
		elif ident == "new":        tok_type = "kw_new"
		elif ident == "null":       tok_type = "kw_null"
		elif ident == "main":       tok_type = "kw_main"
		elif ident == "else":       tok_type = "kw_else"
		elif ident == "this":       tok_type = "kw_this"
		elif ident == "true":       tok_type = "kw_true"
		elif ident == "false":      tok_type = "kw_false"
		elif ident == "class":      tok_type = "kw_class"
		elif ident == "while":      tok_type = "kw_while"
		elif ident == "return":     tok_type = "kw_return"
		elif ident == "readln":     tok_type = "kw_readln"
		elif ident == "println":    tok_type = "kw_println"

		# lowercase the rest of the identififer
		ident = ident[0] + "".join(map(str.lower, ident[1:]))

		return Token(ident, tok_type, loc), stream.drop(len(ident)), loc.advancing(len(ident))

	elif stream.starts_with_one_of("ABCDEFGHIJKLMNOPQRSTUVWXYZ"):
		ident, rest = read_identifier(stream)

		tok_type = "ClassName"
		if ident == "Int":      tok_type = "kw_Int"
		elif ident == "Void":   tok_type = "kw_Void"
		elif ident == "Bool":   tok_type = "kw_Bool"
		elif ident == "String": tok_type = "kw_String"

		# lowercase the rest of the identififer
		ident = ident[0] + "".join(map(str.lower, ident[1:]))

		return Token(ident, tok_type, loc), stream.drop(len(ident)), loc.advancing(len(ident))

	else:
		first_char: str = chr(stream[0])
		tok_type = ""
		if first_char == '+':   tok_type = "Plus"
		elif first_char == '-': tok_type = "Minus"
		elif first_char == '*': tok_type = "Asterisk"
		elif first_char == '/': tok_type = "Slash"
		elif first_char == '.': tok_type = "Period"
		elif first_char == '(': tok_type = "LParen"
		elif first_char == ')': tok_type = "RParen"
		elif first_char == '{': tok_type = "LBrace"
		elif first_char == '}': tok_type = "RBrace"
		elif first_char == '<': tok_type = "LAngle"
		elif first_char == '>': tok_type = "RAngle"
		elif first_char == ';': tok_type = "Semicolon"
		elif first_char == ',': tok_type = "Comma"
		elif first_char == '=': tok_type = "Equal"
		elif first_char == '!': tok_type = "Exclamation"
		else:                   raise ParseException(loc, f"invalid token '{first_char}'")

		return Token(first_char, tok_type, loc), stream.drop(1), loc.advancing(1)
