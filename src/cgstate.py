#!/usr/bin/env python

from __future__ import annotations
from typing import *
from copy import *

from . import ir3
from . import cgopt
from . import cgarm
from . import cgannotate

from .util import options, Location, TCException, CGException, StringView, print_warning, escape_string

import math

POINTER_SIZE    = 4
STACK_ALIGNMENT = 8


class CodegenState:
	def __init__(self, classes: List[ir3.ClassDefn]) -> None:
		self.lines: List[str] = []
		self.strings: Dict[str, int] = dict()

		self.class_layouts: Dict[str, CGClass] = { cls.name: CGClass(self, cls) for cls in classes }

		self.needed_builtins: Set[str] = set()

	def emit_raw(self, line: str) -> None:
		self.lines.append(line)

	def comment(self, line: str = "", indent: int = 1) -> None:
		if line != "":
			self.lines.append('\t' * indent + "@ " + line)
		else:
			self.lines.append("")


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

	def emit_lines(self, lines: List[str]) -> None:
		self.lines += lines

	def get_lines(self) -> List[str]:
		return self.lines


	def require_string_concat_function(self) -> str:
		self.needed_builtins.add(foo := self.get_string_concat_function())
		return foo

	def require_divide_function(self) -> str:
		self.needed_builtins.add(foo := self.get_divide_function())
		return foo

	def require_readln_int_function(self) -> str:
		self.needed_builtins.add(foo := self.get_readln_int_function())
		return foo

	def require_readln_bool_function(self) -> str:
		self.needed_builtins.add(foo := self.get_readln_bool_function())
		return foo

	def require_readln_string_function(self) -> str:
		self.needed_builtins.add(foo := self.get_readln_string_function())
		return foo


	def get_string_concat_function(self) -> str:
		return "__string_concat"

	def get_divide_function(self) -> str:
		return "__divide_int"

	def get_readln_int_function(self) -> str:
		return "__readln_int"

	def get_readln_bool_function(self) -> str:
		return "__readln_bool"

	def get_readln_string_function(self) -> str:
		return "__readln_string"


class VarLoc:
	def __init__(self, name: str, ty: str) -> None:
		self.reg: Optional[cgarm.Register] = None
		self.ofs: Optional[int] = None
		self.name: str = name
		self.type: str = ty

	def set_stack(self, ofs: int) -> VarLoc:
		self.ofs = ofs
		return self

	def set_register(self, register: cgarm.Register) -> VarLoc:
		self.reg = register
		return self

	def clear_register(self) -> VarLoc:
		self.reg = None
		return self

	def clear_stack(self) -> VarLoc:
		self.ofs = None
		return self

	def register(self) -> cgarm.Register:
		if self.reg is None:
			raise CGException(f"variable '{self.name}' has no register")

		return cast(cgarm.Register, self.reg)

	def stack_ofs(self) -> int:
		if self.ofs is None:
			raise CGException(f"variable '{self.name}' has no spill location")

		return cast(int, self.ofs)

	def have_register(self) -> bool:
		return self.reg is not None

	def have_stack(self) -> bool:
		return self.ofs is not None

	def valid(self) -> bool:
		return (self.reg is not None) or (self.ofs is not None)





class FuncState:
	def __init__(self, cs: CodegenState, method: ir3.FuncDefn, assignments: Dict[str, str],
		spills: Set[str], reg_ranges: Dict[str, Set[int]]) -> None:

		self.cs = cs
		self.locations: Dict[str, VarLoc] = dict()
		self.instructions: List[cgarm.Instruction] = []

		self.method = method
		self.exit_label = f".{method.name}_exit"
		self.next_annotation = ""

		frame_size: int = 0

		assigns = { k: cgarm.Register(assignments[k]) for k in assignments }


		# locals shadow parameters, which means that we should do the params first.
		# note that we don't need to worry about stuff not fitting in 1 register, since everything is <= 4 bytes.
		# note also that params never affect our local frame.

		# since we opt to not use the frame pointer, this is how the stack frame is laid out:
		# the stack_loc of a variable is always with reference to the *imaginary stack frame*.
		# we can always calculate this value from the current rsp, because we don't have allocas.
		#
		# so caller-stack-params (ie. arg 5 onwards) have a positive offset from the imaginary frame,
		# and the local spill area has a negative offset. bools take up 4 bytes on the stack, because there's
		# not much benefit to optimising that part, and it takes a lot of effort.

		for i, param in enumerate(method.params):
			if param.name in set(map(lambda x: x.name, method.vars)):
				continue

			ploc = VarLoc(param.name, param.type)
			if i < 4:
				arg_reg = cgarm.Register(f"a{i + 1}")
				if param.name in spills:
					# note that we don't insert code to spill it, because our pseudo-op SpillVariable
					# should have already been inserted on spills.
					stack_loc = -(frame_size + 4)
					ploc.set_stack(stack_loc)
					frame_size += POINTER_SIZE

				if param.name in assignments:
					if assignments[param.name] != arg_reg:
						self.emit(cgarm.mov(assigns[param.name], arg_reg))

					ploc.set_register(assigns[param.name])

				# if the reg name is not spilled and not assigned, we can safely
				# infer that it is not used anywhere, so we can just... ignore it.

			else:
				# these arguments are passed on the stack. these are positive offsets from bp,
				# since they are "above" the current stack frame.
				ploc.set_stack(8 + (i - 4) * 4)

				# these still have registers
				if param.name in assigns:
					ploc.set_register(assigns[param.name])

			self.locations[param.name] = ploc


		# note the negative frame_size here (since the stack grows down, and bp is nearer the top of the stack).
		# TODO: this makes bools 4 bytes
		for var in method.vars:
			ploc = VarLoc(var.name, var.type)

			# note that spilling and being assigned something are not mutually exclusive. now that we
			# have spill/restore pseudo-ops, scratch registers are no longer necessary, which means that
			# spilled variables still need a register assigned, just that their live ranges are very short.
			if var.name in spills:
				stack_loc = -(frame_size + 4)
				ploc.set_stack(stack_loc)
				frame_size += POINTER_SIZE

			if var.name in assigns:
				ploc.set_register(assigns[var.name])

			# same deal here; if it's not spilled or assigned a reg, then we can
			# deduce that it is simply not used.

			self.locations[var.name] = ploc


		self.frame_size: int = STACK_ALIGNMENT * ((frame_size + STACK_ALIGNMENT - 1) // STACK_ALIGNMENT)

		# we already know which registers are touched.
		self.used_regs: Set[str] = set(map(lambda r: r.name, assigns.values()))

		self.reg_live_ranges = reg_ranges

		self.assigns: Dict[str, cgarm.Register] = assigns
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


	def calculate_stack_offset(self, ofs: int) -> int:
		# starting from the current sp, we must *ADD* our frame size,
		# and *ADD* the extra_offset, and *ADD* the actual offset.
		return ofs + self.frame_size + self.stack_extra_offset


	def load_stack_location(self, var: str, reg: cgarm.Register) -> None:
		ofs = self.calculate_stack_offset(self.get_location(var).stack_ofs())
		self.emit(cgarm.load(reg, cgarm.Memory(cgarm.SP, ofs)))

	def store_stack_location(self, var: str, reg: cgarm.Register) -> None:
		ofs = self.calculate_stack_offset(self.get_location(var).stack_ofs())
		self.emit(cgarm.store(reg, cgarm.Memory(cgarm.SP, ofs)))



	# the reason that we have to assert we have a register, even when we're spilling, is because
	# we must spill from somewhere. by the virtue of inserting these spill/reload pseudo-ops, the
	# live range of the var should have split, giving us a variable to assign it.
	def spill_variable(self, var: str) -> None:
		loc = self.get_location(var)
		if not loc.have_register():
			raise CGException(f"no register to spill '{var}'")

		self.store_stack_location(var, loc.register())


	def restore_variable(self, var: str) -> None:
		loc = self.get_location(var)
		if not loc.have_register():
			raise CGException(f"could not restore '{var}'")

		self.load_stack_location(var, loc.register())



	def stack_push(self, reg: cgarm.Register) -> None:
		self.emit(cgarm.store(reg, cgarm.Memory(cgarm.SP, -4, post_incr = True)))
		self.stack_extra_offset += 4

	def stack_push_32n(self, num: int) -> cgarm.Instruction:
		self.stack_extra_offset += (4 * num)
		return self.emit(cgarm.sub(cgarm.SP, cgarm.SP, cgarm.Constant(num * 4)))

	def stack_pop_32n(self, num: int) -> cgarm.Instruction:
		self.stack_extra_offset -= (4 * num)
		assert self.stack_extra_offset >= 0

		return self.emit(cgarm.add(cgarm.SP, cgarm.SP, cgarm.Constant(num * 4)))

	def stack_extra_32n(self, num: int) -> None:
		self.stack_extra_offset += (4 * num)

	def current_stack_offset(self) -> int:
		return self.frame_size + self.stack_extra_offset


	def mangle_label(self, label: str) -> str:
		if label[0] == '.':
			label = label[1:]

		return f".{self.method.name}_{label}"


	def emit_label(self, name: str) -> None:
		self.emit(cgarm.label(self.mangle_label(name)))


	def emit(self, instr: cgarm.Instruction) -> cgarm.Instruction:
		if self.next_annotation != "":
			instr.annotate(self.next_annotation)
			self.next_annotation = ""

		self.instructions.append(instr)
		return instr

	# annotate the *NEXT* instruction that gets emitted.
	def annotate_next(self, msg: str) -> None:
		self.next_annotation = msg


	def branch_to_exit(self) -> None:
		self.emit(cgarm.branch(self.exit_label))


	def finalise(self) -> List[str]:
		if not options.annotations_enabled():
			for i in self.instructions:
				i.clear_annotations()

		final_insts = [
			*self.get_prologue(),
			*self.instructions,
			*self.get_epilogue()
		]

		header = [
			f".global {self.method.name}",
			f".type {self.method.name}, %function",
			f"{self.method.name}:"
		]

		annots = []
		if options.annotations_enabled():
			assign_names = { k: v.name for k, v in self.assigns.items() }

			annot_assigns, annot_spills = cgannotate.annotate_reg_allocs(assign_names, self.spilled)
			for s in annot_spills:
				annots.append(f"\t@ {s}")
			for a in annot_assigns:
				annots.append(f"\t@ {a}")

		return [
			*header,
			*annots,
			*map(lambda x: str(x) if x.is_label else f"\t{x}", final_insts)
		]



	def get_prologue(self) -> List[cgarm.Instruction]:
		callee_saved = ["v1", "v2", "v3", "v4", "v5", "v6", "v7", "fp"]
		restore = self.used_regs.intersection(callee_saved)

		instrs = []

		# if the frame size is 0, combine the two pushes into one
		if self.frame_size > 0:
			instrs.append(cgarm.store_multiple(cgarm.SP, [ cgarm.LR ]))
			instrs.append(cgarm.sub(cgarm.SP, cgarm.SP, cgarm.Constant(self.frame_size)))

			if len(restore) > 0:
				instrs.append(cgarm.store_multiple(cgarm.SP, map(cgarm.Register, restore)))

		else:
			instrs.append(cgarm.store_multiple(cgarm.SP, [ cgarm.LR, *map(cgarm.Register, restore) ]))


		return instrs


	def get_epilogue(self) -> List[cgarm.Instruction]:
		callee_saved = ["v1", "v2", "v3", "v4", "v5", "v6", "v7", "fp"]
		restore = self.used_regs.intersection(callee_saved)

		instrs = []
		instrs.append(cgarm.label(self.exit_label))

		if self.frame_size > 0:
			if len(restore) > 0:
				instrs.append(cgarm.load_multiple(cgarm.SP, map(cgarm.Register, restore)))

			instrs.append(cgarm.add(cgarm.SP, cgarm.SP, cgarm.Constant(self.frame_size)))
			instrs.append(cgarm.load_multiple(cgarm.SP, [ cgarm.PC ]))

		else:
			instrs.append(cgarm.load_multiple(cgarm.SP, [ cgarm.PC, *map(cgarm.Register, restore) ]))


		return instrs







class CGClass:
	def __init__(self, cs: CodegenState, cls: ir3.ClassDefn) -> None:
		self.base = cls

		# since types are either 4 bytes or 1 byte, our life is actually quite easy. we just
		# shove all the bools to the back...
		self.fields: Dict[str, int] = dict()

		# put bools at the end so they pack better.
		offset = 0
		for field in filter(lambda x: x.type != "Bool", self.base.fields):
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
