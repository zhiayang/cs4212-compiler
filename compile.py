#!/usr/bin/env python

import sys
import os

from src.util import *
from src.util import options

from src import typecheck
from src import codegen
from src import parser
from src import lexer
from src import ast


print_ir3 = False

def parse_args(args: List[str]) -> Tuple[str, str]:
	global print_ir3

	input_file: Optional[str] = None
	output_file: Optional[str] = None

	if "--help" in args:
		print_usage()
		sys.exit(0)

	while len(args) > 0:
		if (args[0] == "--opt") or (args[0] == "-O"):
			options.enable_optimisations()

		elif (args[0] == "-a") or (args[0] == "--annotate"):
			options.enable_annotations()

		elif (args[0] == "-na") or (args[0] == "--no-annotate"):
			options.disable_annotations()

		elif (args[0] == "-v") or (args[0] == "--verbose"):
			options.enable_verbose()

		elif (args[0] == "--dump-ir3"):
			print_ir3 = True

		elif (args[0] == "--dump-ir3-lowered"):
			options.enable_print_lowered_ir(True)

		elif args[0] == "-o":
			if output_file is not None:
				print(f"error: multiple output names")
				sys.exit(1)

			if len(args) == 1:
				print(f"error: expected filename after '-o'")
				sys.exit(1)

			output_file = args[1]
			args = args[1:]

		else:
			if input_file is not None:
				print(f"error: multiple input files")
				sys.exit(1)

			input_file = args[0]

		args = args[1:]

	if input_file is None:
		print(f"error: no input files provided")
		sys.exit(1)

	if output_file is None:
		output_file = os.path.splitext(input_file)[0] + ".s"

	return cast(str, input_file), cast(str, output_file)


def print_usage():
	print(f"usage: ./compile.py [options] <source_file>")
	print("""
options:
    --opt           -O      enable optimisations
    --annotate      -a      enable annotations on the generated assembly
    --no-annotate   -na     disable annotations
    --verbose       -v      print logging statements (mostly optimisation-related)
    --dump-ir3              print the generated ir3 to stdout
    --dump-ir3-lowered      print the lowered ir3 to stdout
    -o <filename>           set the output filename
""")


def parse_file(filename: str) -> ast.Program:
	with open(filename, "rb") as file:
		stream: StringView = StringView(file.read())
		return parser.parse_program(parser.ParserState(filename, stream))


if __name__ == "__main__":
	if len(sys.argv) < 2:
		print_usage()
		sys.exit(1)

	input_file, output_file = parse_args(sys.argv[1:])

	prog = parse_file(input_file)
	ir3p = typecheck.typecheck_program(prog)

	if print_ir3:
		print(ir3p)

	asms = codegen.codegen(ir3p, ' '.join(sys.argv))

	with open(output_file, "w") as f:
		f.write('\n'.join(asms))
		f.write("\n")
