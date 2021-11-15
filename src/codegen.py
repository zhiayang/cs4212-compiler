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
		self.classes: Dict[str, ir3.ClassDefn] = { cls.name: cls for cls in classes }
		self.builtin_sizes = { "Void": 0, "Int": 4, "Bool": 4, "String": 4 }

		self.prologue_label = ""
		self.current_method: ir3.FuncDefn
		self.strings: Dict[str, int] = dict()

	# gets the size of a type, but objects are always size 4
	def sizeof_type_pointers(self, name: str) -> int:
		if name in self.builtin_sizes:
			return self.builtin_sizes[name]

		if name not in self.classes:
			raise CGException(f"unknown class '{name}'")

		return POINTER_SIZE

	def emit(self, line: str, indent: int = 1) -> None:
		self.lines.append('\t' * indent + line)

	def comment(self, line: str = "", indent: int = 1) -> None:
		if line != "":
			self.lines.append('\t' * indent + "@ " + line)
		else:
			self.lines.append("")

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



class CGClass:
	def __init__(self, cs: CodegenState, cls: ir3.ClassDefn) -> None:
		self.base = cls

		# since types are either 4 bytes or 1 byte, our life is actually quite easy. we just
		# shove all the bools to the back...
		self.fields: Dict[str, int] = dict()

		# TODO: this makes bools 4 bytes even in structs
		offset = 0
		for field in self.base.fields:
			assert cs.sizeof_type_pointers(field.type) == POINTER_SIZE
			self.fields[field.name] = offset
			offset += POINTER_SIZE

		# round up to the nearest 4 bytes
		self.total_size = POINTER_SIZE * (offset + POINTER_SIZE - 1) // POINTER_SIZE




class VarLoc:
	def __init__(self) -> None:
		self.reg: Optional[str] = None
		self.ofs: Optional[int] = None
		self.backup_ofs: Optional[int] = None
		self.stale_mem: bool = False

	def set_stack(self, ofs: int) -> VarLoc:
		self.ofs = ofs
		return self

	def set_register(self, name: str) -> VarLoc:
		self.reg = name
		return self

	def set_stack_backup(self, ofs: int) -> VarLoc:
		self.backup_ofs = ofs
		return self

	def clear_register(self) -> VarLoc:
		self.reg = None
		return self

	def clear_stack(self) -> VarLoc:
		self.ofs = None
		return self

	def switch_to_backup(self) -> VarLoc:
		assert self.have_stack_backup()
		self.ofs = self.backup_ofs
		self.backup_ofs = None
		return self

	def register(self) -> str:
		return cast(str, self.reg)

	def stack_ofs(self) -> int:
		return cast(int, self.ofs)

	def backup_stack_ofs(self) -> int:
		return cast(int, self.backup_ofs)

	def have_register(self) -> bool:
		return self.reg is not None

	def have_stack(self) -> bool:
		return self.ofs is not None

	def have_stack_backup(self) -> bool:
		return self.backup_ofs is not None

	def set_reg_modified(self):
		self.stale_mem = True

	def valid(self) -> bool:
		return (self.reg is not None) or (self.ofs is not None)





class VarState:
	def __init__(self, cs: CodegenState, vars: List[ir3.VarDecl], params: List[ir3.VarDecl]) -> None:

		self.cs = cs

		offset: int = 0

		self.locations: Dict[str, VarLoc] = dict()
		self.var_types: Dict[str, str] = dict()

		self.registers: Dict[str, str] = {
			"a1": "", "a2": "", "a3": "", "a4": "",
			"v1": "", "v2": "", "v3": "", "v4": "", "v5": ""
		}


		# note the negative offset here (since the stack grows down, and bp is nearer the top of the stack).
		# TODO: this makes bools 4 bytes
		for var in vars:
			self.var_types[var.name] = var.type
			self.locations[var.name] = VarLoc().set_stack(-offset)
			offset += POINTER_SIZE


		# parameters also need locations, duh. note that we don't need to worry about
		# stuff not fitting in 1 register, since everything is <= 4 bytes.
		param_num: int = 1
		for param in params:
			ploc = VarLoc()
			if param_num < 4:
				reg_name = f"a{param_num}"
				self.registers[reg_name] = param.name

				ploc.set_register(reg_name)

				# we don't want to waste time copying from the register to the stack,
				# so set the stack location as stale
				ploc.set_reg_modified()
				ploc.set_stack(-offset)

				offset += POINTER_SIZE

			else:
				# these arguments are passed on the stack. these are positive offsets from bp,
				# since they are "above" the current stack frame.
				ploc.set_stack(8 + (param_num - 4 - 1) * 4)

				# we need a backup location so that this variable can always be spilled. we obviously
				# can't write to the caller-owned memory "above" rbp, so we need space on the current frame.
				ploc.set_stack_backup(-offset)
				offset += POINTER_SIZE


			self.locations[param.name] = ploc
			self.var_types[param.name] = param.type

			param_num += 1


		self.frame_size: int = STACK_ALIGNMENT * ((offset + STACK_ALIGNMENT - 1) // STACK_ALIGNMENT)
		self.touched: Set[str] = set()



	def spill_register(self, reg: str):
		old_var = self.registers[reg]
		if old_var is not None and old_var != "$scratch":
			# unset the current register from the loc first
			self.locations[old_var].clear_register()

			# do the spill
			if self.locations[old_var].stale_mem:
				# if the thing was a stack parameter (and we wrote to it), then we need
				# to store not to the original stack location, but to the "backup" location
				if self.locations[old_var].have_stack_backup():
					self.locations[old_var].switch_to_backup()

				stk_ofs = self.locations[old_var].stack_ofs()
				self.cs.emit(f"str {reg}, [fp, #{stk_ofs}]")


	def find_free_register(self) -> Optional[str]:
		for (reg, cur) in self.registers.items():
			if cur == "":
				return reg
		return None

	def get_register_to_spill(self) -> str:
		# TODO: choose a register to spill using a more 4head algorithm
		# for now, just spill the first one.
		return next(iter(self.registers))


	def scratch_register(self) -> str:
		free_reg = self.find_free_register()
		if free_reg is not None:
			return free_reg

		spill = self.get_register_to_spill()
		self.spill_register(spill)

		# TODO: use this to prefer spilling scratch registers. anyway there
		# shouldn't be too many of these.
		self.registers[spill] = "$scratch"
		return spill



	# if skip_loads is true, we don't bother loading the old value from the stack to the new register; the
	# assumption is that we will soon store to that register, so there's no point loading anything
	def make_available(self, var: str, skip_loads = False) -> str:
		loc = self.locations[var]

		# if the var is already in a register, use it
		if loc.have_register():
			return loc.register()

		# if we have a free register, load from memory to that register
		free_reg = self.find_free_register()
		if free_reg is not None:
			self.registers[free_reg] = var
			self.locations[var].set_register(free_reg)

			# do a load. stack_ofs is still valid (we can be both)
			if not skip_loads:
				self.cs.emit(f"ldr {free_reg}, [fp, #{loc.stack_ofs()}]")

			self.touched.add(free_reg)
			return free_reg

		# TODO: choose a register to spill using a more 4head algorithm
		# we didn't, so spill something. for now, just spill the first one.
		reg = self.get_register_to_spill()
		self.spill_register(reg)

		# load the new value
		stk_ofs = self.locations[var].stack_ofs()
		if not skip_loads:
			self.cs.emit(f"ldr {reg}, [fp, #{stk_ofs}]")

		# setup the descriptors and stuff
		self.locations[var].set_register(reg)
		self.registers[reg] = var
		self.touched.add(reg)

		return reg







	def emit_prologue(self, cs: CodegenState) -> List[str]:
		callee_saved = set(["v1", "v2", "v3", "v4", "v5", "v6", "v7"])
		restore = sorted(list(callee_saved.intersection(self.touched)))
		if len(restore) == 0:
			restore_str = ""
		else:
			restore_str = (", ".join(restore)) + ", "

		cs.emit(f"stmfd sp!, {{{restore_str}fp, lr}}")
		cs.emit(f"mov fp, sp")
		cs.emit(f"sub sp, sp, #{self.frame_size}")
		cs.comment("prologue")
		cs.comment()

		return restore


	def emit_epilogue(self, cs: CodegenState, restore: List[str]) -> None:
		if len(restore) == 0:
			restore_str = ""
		else:
			restore_str = (", ".join(restore)) + ", "

		cs.comment()
		cs.comment("epilogue")
		cs.emit(f"{cs.prologue_label}:", indent = 0)
		cs.emit(f"add sp, sp, #{self.frame_size}")
		cs.emit(f"ldmfd sp!, {{{restore_str}fp, pc}}")











# returns (string, is_constant)
def codegen_value(cs: CodegenState, vs: VarState, operand: ir3.Value) -> Tuple[str, bool, str]:
	if isinstance(operand, ir3.ConstantInt):
		return f"#{operand.value}", True, "Int"

	elif isinstance(operand, ir3.ConstantBool):
		return f"#{0 if not operand.value else 1}", True, "Bool"

	elif isinstance(operand, ir3.ConstantNull):
		return f"#0", True, "$NullObject"

	elif isinstance(operand, ir3.ConstantString):
		scr = vs.scratch_register()
		cs.emit(f"ldr {scr}, ={cs.add_string(operand.value)}")
		return scr, True, "String"

	elif isinstance(operand, ir3.VarRef):
		return vs.make_available(operand.name), False, vs.var_types[operand.name]

	else:
		assert False and "unreachable"



def codegen_binop(cs: CodegenState, vs: VarState, expr: ir3.BinaryOp, dest_reg: str):
	if expr.strs:
		# TODO: string concatenation
		cs.comment("NOT IMPLEMENTED (string concat)")
		return

	elif expr.op == "/":
		# TODO: long division routine
		cs.comment("NOT IMPLEMENTED (division)")
		return




	lhs, lc, _ = codegen_value(cs, vs, expr.lhs)
	rhs, rc, _ = codegen_value(cs, vs, expr.rhs)

	if lc and rc:
		raise TCException(expr.loc, "somehow, constant folding failed")


	# turns out all of these need unique paths ><
	if expr.op == "+":
		if lc:
			lhs, rhs = rhs, lhs

		cs.emit(f"add {dest_reg}, {lhs}, {rhs}")

	elif expr.op == "-":
		flip = False
		if lc:
			lhs, rhs = rhs, lhs
			flip = True

		cs.emit(f"{'rsb' if negate else 'sub'} {dest_reg}, {lhs}, {rhs}")

	elif expr.op == "*":
		# ok so, we can't have an immediate in a multiply instruction because arm
		# instruction encoding is inferior. since it's a constant though, we just
		# emit the required number of adds and shifts...

		if lc or rc:
			# keep the constant on the right i guess
			if lc:
				lhs, rhs = rhs, lhs

			# anyway this should be an integer
			constant_thing = expr.lhs if lc else expr.rhs

			assert isinstance(constant_thing, ir3.ConstantInt)
			mult: int = constant_thing.value


			negate: bool = False
			if mult == 0:
				cs.emit(f"add {dest_reg}, {lhs}, #0")
				return

			elif mult < 0:
				negate = True

			# to be not entirely 3 head, optimise by trying to shift if possible.
			p2 = 1 << math.floor(math.log2(mult))
			mult -= p2

			cs.emit(f"mov {dest_reg}, {lhs}, lsl #{p2}")

			while mult > 0:
				cs.emit(f"add {dest_reg}, {dest_reg}, {lhs}")
				mult -= 1

			if negate:
				cs.emit(f"rsb {dest_reg}, {dest_reg}, #0")

		else:
			cs.emit(f"mul {dest_reg}, {lhs}, {rhs}")

	elif expr.op in ["==", "!=", "<=", ">=", "<", ">"]:
		instr_map = {"==": "eq", "!=": "ne", "<=": "le", ">=": "ge", "<": "lt", ">": "gt"}

		cs.emit(f"eor {dest_reg}, {dest_reg}, {dest_reg}")
		cs.emit(f"mov{instr_map[expr.op]} {dest_reg}, #1")

	else:
		cs.comment(f"NOT IMPLEMENTED (binop '{expr.op}')")




def codegen_expr(cs: CodegenState, vs: VarState, expr: ir3.Expr, dest_reg: str):
	if isinstance(expr, ir3.BinaryOp):
		codegen_binop(cs, vs, expr, dest_reg)

	elif isinstance(expr, ir3.ValueExpr):
		# we might potentially want to abstract this out, but for now idgaf
		operand, _, _ = codegen_value(cs, vs, expr.value)
		cs.emit(f"mov {dest_reg}, {operand}")

	else:
		cs.comment(f"NOT IMPLEMENTED (expression)")




def codegen_assign(cs: CodegenState, vs: VarState, assign: ir3.AssignOp):
	dest_reg = vs.make_available(assign.lhs, skip_loads=True)
	codegen_expr(cs, vs, assign.rhs, dest_reg)




def codegen_return(cs: CodegenState, vs: VarState, stmt: ir3.ReturnStmt):
	if stmt.value is not None:
		value, _, _ = codegen_value(cs, vs, stmt.value)
		cs.emit(f"mov a1, {value}")

	cs.emit(f"b {cs.prologue_label}")


def codegen_uncond_branch(cs: CodegenState, vs: VarState, ubr: ir3.Branch):
	cs.emit(f"b {cs.mangle_label(ubr.label)}")


def codegen_cond_branch(cs: CodegenState, vs: VarState, cbr: ir3.CondBranch):
	if isinstance(cbr.cond, ir3.RelOp):
		cs.comment("NOT IMPLEMENTED (relop branch)")

	else:
		value, const, _ = codegen_value(cs, vs, cbr.cond)
		if const:
			cs.comment("NOT IMPLEMENTED (const branch)")

		else:
			cs.emit(f"cmp {value}, #0")
			cs.emit(f"bne {cs.mangle_label(cbr.label)}")


def codegen_println(cs: CodegenState, vs: VarState, stmt: ir3.PrintLnCall):
	value, const, ty = codegen_value(cs, vs, stmt.value)

	if const:
		if ty == "String":
			vs.spill_register("a1")
			cs.emit(f"mov a1, {value}")

			# for strings specifically, increment by 4 to skip the length. the value is a pointer anyway.
			cs.emit(f"add a1, a1, #4")
			cs.emit(f"bl puts(PLT)")

		elif ty == "Bool":
			pass
		elif ty == "Int":
			pass
		elif ty == "$NullObject":
			pass
	else:
		pass



def codegen_stmt(cs: CodegenState, vs: VarState, stmt: ir3.Stmt):
	cs.comment(str(stmt))
	if isinstance(stmt, ir3.AssignOp):
		codegen_assign(cs, vs, stmt)

	elif isinstance(stmt, ir3.ReturnStmt):
		codegen_return(cs, vs, stmt)

	elif isinstance(stmt, ir3.PrintLnCall):
		codegen_println(cs, vs, stmt)

	elif isinstance(stmt, ir3.Branch):
		codegen_uncond_branch(cs, vs, stmt)

	elif isinstance(stmt, ir3.CondBranch):
		codegen_cond_branch(cs, vs, stmt)

	else:
		cs.comment("NOT IMPLEMENTED")



def codegen_method(cs: CodegenState, method: ir3.FuncDefn):
	cs.set_current_method(method)

	# time to start emitting code...
	cs.emit(f".global {method.name}", indent = 0)
	cs.emit(f".type {method.name}, %function", indent = 0)
	cs.emit(f"{method.name}:", indent = 0)

	# start sending stuff to the gulag, from which we will later rescue them
	cs.begin_scope()
	vs = VarState(cs, method.vars, method.params)

	# the way we handle returns (which isn't a good way i admit) is to just set the return
	# value in a1 (if any), then branch to the epilogue. so, emit a label here:
	cs.set_prologue(f".{method.name}_epilogue")

	for block in method.blocks:
		cs.emit(f"{cs.mangle_label(block.name)}:", indent = 0)
		for stmt in block.stmts:
			codegen_stmt(cs, vs, stmt)

	# rescue the stmts we put in the gulag
	fn_stmts = cs.get_scoped()
	cs.end_scope()

	# now that we know which registers were used, we can do the appropriate save/restore.
	# at this point the actual body has not been emitted (it's in `fn_stmts`).
	restore = vs.emit_prologue(cs)

	cs.emit_lines(fn_stmts)

	vs.emit_epilogue(cs, restore)
	cs.emit(f"\n")



















def codegen(prog: ir3.Program, opt: bool) -> List[str]:
	cs = CodegenState(opt, prog.classes)

	cs.emit(".text", indent = 0)
	for method in prog.funcs:
		if method.name == "main":
			method.name = "main_dummy"

		codegen_method(cs, method)

	# insert code to call main_dummy from the "real" main that handles the
	# return value and stuff.
	cs.emit("""
.global main
.type main, %function
main:
	str lr, [sp, #-4]!
	bl main_dummy

	@ set the return code to 0
	mov a1, #0
	ldr pc, [sp], #4
""")


	cs.emit(".data", indent = 0)
	for string, id in cs.strings.items():
		cs.emit(f".string{id}:", indent = 0)
		cs.emit(f".word {len(string)}")
		cs.emit(f'.asciz "{escape_string(string)}"')
		cs.comment()


	return cs.lines

