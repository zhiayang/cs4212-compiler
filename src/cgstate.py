#!/usr/bin/env python

from __future__ import annotations
from typing import *
from copy import *

from . import ir3

from .util import Location, TCException, CGException, StringView, print_warning, escape_string

import math

POINTER_SIZE    = 4
STACK_ALIGNMENT = 8


class CodegenState:
	def __init__(self, opt: bool, classes: List[ir3.ClassDefn]) -> None:
		self.opt = opt
		self.lines: List[str] = []
		self.classes_defs: Dict[str, ir3.ClassDefn] = { cls.name: cls for cls in classes }
		self.builtin_sizes = { "Void": 0, "Int": 4, "Bool": 4, "String": 4 }

		self.prologue_label = ""
		self.current_method: ir3.FuncDefn
		self.strings: Dict[str, int] = dict()

		self.class_layouts: Dict[str, CGClass] = { cls.name: CGClass(self, cls) for cls in classes }

	# gets the size of a type, but objects are always size 4
	def sizeof_type_pointers(self, name: str) -> int:
		if name in self.builtin_sizes:
			return self.builtin_sizes[name]

		if name not in self.classes_defs:
			raise CGException(f"unknown class '{name}'")

		return POINTER_SIZE

	def emit(self, line: str, indent: int = 1) -> None:
		self.lines.append('\t' * indent + line)

	def comment(self, line: str = "", indent: int = 1) -> None:
		if line != "":
			self.lines.append('\t' * indent + "@ " + line)
		else:
			self.lines.append("")

	def comment_line(self, msg: str) -> None:
		padding = 40 - len(self.lines[-1])
		if padding > 0:
			self.lines[-1] += (' ' * padding)

		if '@' not in self.lines[-1]:
			msg = f"@ {msg}"

		self.lines[-1] += msg

	def set_prologue(self, label: str) -> None:
		self.prologue_label = label

	def set_current_method(self, method: ir3.FuncDefn) -> None:
		self.current_method = method

	def mangle_label(self, label: str) -> str:
		if label[0] == '.':
			label = label[1:]
		return f".{self.current_method.name}_{label}"

	# not re-entrant, but then again nothing in this compiler is reentrant
	# basically this makes all emit calls not add to the big list of instructions
	# immediately; this is so we have a chance to insert the prologue/epilogue.
	def begin_scope(self) -> None:
		self.old_lines = self.lines
		self.lines = []

	# this gets the lines that were sent to the gulag
	def get_scoped(self) -> List[str]:
		return self.lines

	# this ends the scope, *discarding* any lines that were in the gulag
	def end_scope(self) -> None:
		self.lines = self.old_lines

	def emit_lines(self, lines: List[str]) -> None:
		self.lines += lines

	# returns the label of the thing
	def add_string(self, s: str) -> str:
		if s in self.strings:
			return f".string{self.strings[s]}"
		else:
			i = len(self.strings)
			self.strings[s] = i
			return f".string{i}"


	def get_class_layout(self, name: str) -> CGClass:
		return self.class_layouts[name]






class VarLoc:
	def __init__(self, ty: str) -> None:
		self.reg: Optional[str] = None
		self.ofs: Optional[int] = None
		self.type: str = ty

	def set_stack(self, ofs: int) -> VarLoc:
		self.ofs = ofs
		return self

	def set_register(self, name: str) -> VarLoc:
		self.reg = name
		return self

	def clear_register(self) -> VarLoc:
		self.reg = None
		return self

	def clear_stack(self) -> VarLoc:
		self.ofs = None
		return self

	def register(self) -> str:
		return cast(str, self.reg)

	def stack_ofs(self) -> int:
		return cast(int, self.ofs)

	def have_register(self) -> bool:
		return self.reg is not None

	def have_stack(self) -> bool:
		return self.ofs is not None

	def valid(self) -> bool:
		return (self.reg is not None) or (self.ofs is not None)





class VarState:
	def __init__(self, cs: CodegenState, vars: List[ir3.VarDecl], params: List[ir3.VarDecl],
		assignments: Dict[str, str], spills: Set[str], reg_ranges: Dict[str, Set[int]]) -> None:

		self.cs = cs
		self.locations: Dict[str, VarLoc] = dict()

		frame_size: int = 0


		# locals shadow parameters, which means that we should do the params first.
		# note that we don't need to worry about stuff not fitting in 1 register, since everything is <= 4 bytes.

		# note also that params never affect our local frame.
		for i, param in enumerate(params):
			if param.name in set(map(lambda x: x.name, vars)):
				continue

			ploc = VarLoc(param.type)
			if i < 4:
				arg_reg = f"a{i + 1}"
				if param.name in spills:
					# fp[0] is actually the lr, so we start from fp - 4

					# note that we don't insert code to spill it, because our pseudo-op SpillVariable
					# should have already been inserted on spills.
					stack_loc = -(frame_size + 4)
					ploc.set_stack(stack_loc)
					frame_size += POINTER_SIZE

				if param.name in assignments:
					if assignments[param.name] != arg_reg:
						cs.emit(f"mov {assignments[param.name]}, {arg_reg}")

					ploc.set_register(assignments[param.name])

				# if the reg name is not spilled and not assigned, we can safely
				# infer that it is not used anywhere, so we can just... ignore it.

			else:
				# these arguments are passed on the stack. these are positive offsets from bp,
				# since they are "above" the current stack frame.
				ploc.set_stack(8 + (i - 4) * 4)

				# these still have registers
				if param.name in assignments:
					ploc.set_register(assignments[param.name])

			self.locations[param.name] = ploc


		# note the negative frame_size here (since the stack grows down, and bp is nearer the top of the stack).
		# TODO: this makes bools 4 bytes
		for var in vars:
			ploc = VarLoc(var.type)

			# note that spilling and being assigned something are not mutually exclusive. now that we
			# have spill/restore pseudo-ops, scratch registers are no longer necessary, which means that
			# spilled variables still need a register assigned, just that their live ranges are very short.
			if var.name in spills:
				stack_loc = -(frame_size + 4)
				ploc.set_stack(stack_loc)
				frame_size += POINTER_SIZE

			if var.name in assignments:
				ploc.set_register(assignments[var.name])

			# same deal here; if it's not spilled or assigned a reg, then we can
			# deduce that it is simply not used.

			self.locations[var.name] = ploc


		self.frame_size: int = STACK_ALIGNMENT * ((frame_size + STACK_ALIGNMENT - 1) // STACK_ALIGNMENT)

		# we already know which variables are touched.
		self.touched: Set[str] = set(assignments.values())

		self.reg_live_ranges = reg_ranges
		self.spilled: Set[str] = spills

		self.stack_extra_offset = 0


	def is_var_used(self, var: str) -> bool:
		return (var in self.locations) and (self.locations[var].valid())

	def get_type(self, var: str) -> str:
		return self.locations[var].type

	def get_location(self, var: str) -> VarLoc:
		return self.locations[var]

	def is_register_live(self, reg: str, stmt: int) -> bool:
		return (reg in self.reg_live_ranges) and (stmt in self.reg_live_ranges[reg])

	def push_extra(self, num: int) -> None:
		self.stack_extra_offset += num

	def pop_extra(self, num: int) -> None:
		self.stack_extra_offset -= num
		assert self.stack_extra_offset >= 0


	def load_var(self, var: str) -> str:
		# because of our pseudo-ops, there *must* be a register for this guy.
		loc = self.get_location(var)
		if not loc.have_register():
			print(f"no reg for '{var}'")
		assert loc.have_register()

		reg = loc.register()

		# if this was a spilled var, we must load it from memory first.
		if var in self.spilled:
			self.cs.emit(f"ldr {reg}, [fp, #{self.get_location(var).stack_ofs()}]")
			self.cs.comment_line(f"restore {var}")

		return reg


	def make_dest_available(self, var: str) -> str:
		loc = self.get_location(var)
		if not loc.have_register():
			raise CGException(f"did not get register for '{var}'")

		# because of our pseudo-ops, there *must* be a register for this guy.
		return loc.register()

	def writeback_dest(self, var: str, dest_reg: str) -> None:
		loc = self.get_location(var)

		if var in self.spilled and self.is_var_used(var):
			self.cs.emit(f"str {dest_reg}, [fp, #{loc.stack_ofs()}]")
			self.cs.comment_line(f"spill/wb {var}")



	def emit_prologue(self, cs: CodegenState) -> None:
		callee_saved = set(["v1", "v2", "v3", "v4", "v5", "v6", "v7"])
		restore = sorted(list(callee_saved.intersection(self.touched)))
		if len(restore) == 0:
			restore_str = ""
		else:
			restore_str = (", ".join(restore))

		cs.emit(f"stmfd sp!, {{fp, lr}}")
		cs.emit(f"mov fp, sp")
		cs.emit(f"sub sp, sp, #{self.frame_size}")

		if restore_str != "":
			cs.emit(f"stmfd sp!, {{{restore_str}}}")

		cs.comment("prologue")
		cs.comment()


	def emit_epilogue(self, cs: CodegenState) -> None:
		callee_saved = set(["v1", "v2", "v3", "v4", "v5", "v6", "v7"])
		restore = sorted(list(callee_saved.intersection(self.touched)))
		if len(restore) == 0:
			restore_str = ""
		else:
			restore_str = (", ".join(restore))

		cs.comment()
		cs.comment("epilogue")
		cs.emit(f"{cs.prologue_label}:", indent = 0)

		if restore_str != "":
			cs.emit(f"ldmfd sp!, {{{restore_str}}}")

		cs.emit(f"add sp, sp, #{self.frame_size}")
		cs.emit(f"ldmfd sp!, {{fp, pc}}")





class CGClass:
	def __init__(self, cs: CodegenState, cls: ir3.ClassDefn) -> None:
		self.base = cls

		# since types are either 4 bytes or 1 byte, our life is actually quite easy. we just
		# shove all the bools to the back...
		self.fields: Dict[str, int] = dict()

		# put bools at the end so they pack better.
		offset = 0
		for field in filter(lambda x: x.type != "Bool", self.base.fields):
			assert cs.sizeof_type_pointers(field.type) == POINTER_SIZE
			self.fields[field.name] = offset
			offset += POINTER_SIZE

		for field in filter(lambda x: x.type == "Bool", self.base.fields):
			self.fields[field.name] = offset
			offset += 1

		# round up to the nearest 4 bytes
		self.total_size = POINTER_SIZE * ((offset + POINTER_SIZE - 1) // POINTER_SIZE)

		if self.total_size == 0:
			self.total_size = POINTER_SIZE


	def size(self) -> int:
		return self.total_size

	def field_offset(self, field: str) -> int:
		return self.fields[field]

	def field_size(self, field: str) -> int:
		# we assume that everything is 4 bytes except for bools which are 1.
		if next(filter(lambda f: f.name == field, self.base.fields)).type == "Bool":
			return 1
		else:
			return 4
