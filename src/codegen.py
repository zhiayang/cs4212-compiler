#!/usr/bin/env python

from __future__ import annotations
from typing import *
from copy import *

from . import ir3

from .util import Location, CGException, StringView, print_warning

POINTER_SIZE    = 4
STACK_ALIGNMENT = 8


class CodegenState:
	def __init__(self, opt: bool, classes: List[ir3.ClassDefn]) -> None:
		self.opt = opt
		self.lines: List[str] = []
		self.classes: Dict[str, ir3.ClassDefn] = { cls.name: cls for cls in classes }
		self.builtin_sizes = { "Void": 0, "Int": 4, "Bool": 1, "String": 4 }

	# gets the size of a type, but objects are always size 4
	def sizeof_type_pointers(self, name: str) -> int:
		if name in self.builtin_sizes:
			return self.builtin_sizes[name]

		if name not in self.classes:
			raise CGException(f"unknown class '{name}'")

		return POINTER_SIZE

	def emit(self, line: str) -> None:
		self.lines.append(line)




class CGClass:
	def __init__(self, cs: CodegenState, cls: ir3.ClassDefn) -> None:
		self.base = cls

		# since types are either 4 bytes or 1 byte, our life is actually quite easy. we just
		# shove all the bools to the back...
		self.fields: Dict[str, int] = dict()

		# i'm not even gonna bother doing an actual sort... just do a 2-pass approach.
		offset = 0
		for field in self.base.fields:
			if field.type == "Bool":
				continue

			assert cs.sizeof_type_pointers(field.type) == POINTER_SIZE
			self.fields[field.name] = offset
			offset += POINTER_SIZE

		for field in self.base.fields:
			if field.type != "Bool":
				continue

			self.fields[field.name] = offset
			offset += 1

		# round up to the nearest 4 bytes
		self.total_size = (offset + POINTER_SIZE - 1) // POINTER_SIZE



class VarState:
	def __init__(self, cs: CodegenState, vars: List[ir3.VarDecl]) -> None:
		self.frame_size: int = 0

		if cs.opt:
			assert False and "not implemented"

		else:
			offset: int = 0
			self.offsets: Dict[str, int] = dict()

			# same deal with the frame, here. just push all bools to the end
			for var in vars:
				if var.type == "Bool":
					continue

				assert cs.sizeof_type_pointers(var.type) == POINTER_SIZE
				self.offsets[var.name] = offset
				offset += POINTER_SIZE

			for var in vars:
				if var.type != "Bool":
					continue

				self.offsets[var.name] = offset
				offset += 1

			self.frame_size = (offset + STACK_ALIGNMENT - 1) // STACK_ALIGNMENT


def codegen_method(cs: CodegenState, method: ir3.FuncDefn):
	vs = VarState(cs, method.vars)

	# time to start emitting code...
	cs.emit(f".global {method.name}")
	cs.emit(f".type {method.name}, %function")
	cs.emit(f"{method.name}:")




	pass




















def codegen(prog: ir3.Program, opt: bool) -> List[str]:
	cs = CodegenState(opt, prog.classes)

	for method in prog.funcs:
		codegen_method(cs, method)

	return cs.lines

