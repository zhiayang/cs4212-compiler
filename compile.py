#!/usr/bin/env python

import sys
import os

from src.util import *
from src import typecheck
from src import codegen
from src import parser
from src import lexer
from src import ast

def parse_file(filename) -> ast.Program:
	with open(sys.argv[1], "rb") as file:
		stream: StringView = StringView(file.read())
		return parser.parse_program(parser.ParserState(sys.argv[1], stream))


if __name__ == "__main__":
	if len(sys.argv) < 2:
		print(f"usage: ./compile.py <source_file>")
		sys.exit(1)

	prog = parse_file(sys.argv[1])
	ir3p = typecheck.typecheck_program(prog)
	asms = codegen.codegen(ir3p, opt=False)

	out_file = os.path.splitext(sys.argv[1])[0] + ".s"
	with open(out_file, "w") as f:
		f.write('\n'.join(asms))
		f.write("\n")
