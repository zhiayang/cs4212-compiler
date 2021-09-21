#!/usr/bin/env python

import sys
from src.util import *
from src import parser

def lex_file(filename):
	with open(sys.argv[1], "rb") as file:
		stream: StringView = StringView(file.read())
		loc: Location = Location(sys.argv[1], 0, 0)
		flag: bool = True

	token_list: list[Token] = []
	while flag:
		tok, rest, loc = read_token(stream, loc)
		stream = rest

		# for this printing thing, we just discard the content of the comment.
		if tok.type == "comment":
			tok.text = "comment"

		token_list.append(tok)
		if tok.type == "EOF":
			flag = False

	for tok in token_list:
		print(tok)


if __name__ == "__main__":
	if len(sys.argv) < 2:
		print(f"usage: ./lex.py <source_file>")
		sys.exit(1)

	lex_file(sys.argv[1])
