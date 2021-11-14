#!/usr/bin/env python

from __future__ import annotations
from typing import *
from copy import *

from . import ir3
from .util import Location, TCException, CGException, StringView, print_warning

import math

POINTER_SIZE    = 4
STACK_ALIGNMENT = 8


class CodegenState:
	def __init__(self, opt: bool, classes: List[ir3.ClassDefn]) -> None:
		self.opt = opt
		self.lines: List[str] = []
		self.classes: Dict[str, ir3.ClassDefn] = { cls.name: cls for cls in classes }
		self.builtin_sizes = { "Void": 0, "Int": 4, "Bool": 1, "String": 4 }

		self.prologue_label = ""

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
		self.total_size = POINTER_SIZE * (offset + POINTER_SIZE - 1) // POINTER_SIZE




class VarLoc:
	def __init__(self) -> None:
		self.reg: Optional[str] = None
		self.ofs: Optional[int] = None

	def set_stack(self, ofs: int) -> VarLoc:
		self.ofs = ofs
		return self

	def set_register(self, name: str) -> VarLoc:
		self.reg = name
		return self

	def clear_register(self) -> VarLoc:
		self.reg = None
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
	def __init__(self, cs: CodegenState, vars: List[ir3.VarDecl], params: List[ir3.VarDecl]) -> None:

		self.cs = cs

		offset: int = 0

		# var_name -> offset
		self.locations: Dict[str, VarLoc] = dict()

		# same deal with the frame, here. just push all bools to the end. note the negative offset here
		# (since the stack grows down, and bp is nearer the top of the stack).
		for var in vars:
			if var.type == "Bool":
				continue

			assert cs.sizeof_type_pointers(var.type) == POINTER_SIZE
			self.locations[var.name] = VarLoc().set_stack(-offset)
			offset += POINTER_SIZE

		for var in vars:
			if var.type != "Bool":
				continue

			self.locations[var.name] = VarLoc().set_stack(-offset)
			offset += 1

		self.registers: Dict[str, str] = {
			"a1": "", "a2": "", "a3": "", "a4": "",
			"v1": "", "v2": "", "v3": "", "v4": "", "v5": ""
		}

		# parameters also need locations, duh. note that we don't need to worry about
		# stuff not fitting in 1 register, since everything is <= 4 bytes.
		param_num: int = 1
		for param in params:
			if param_num < 4:
				reg_name = f"a{param_num}"
				self.registers[reg_name] = param.name
				self.locations[param.name] = VarLoc().set_register(reg_name)
			else:
				# these arguments are passed on the stack. these are positive offsets from bp,
				# since they are "above" the current stack frame.
				self.locations[param.name] = VarLoc().set_stack(8 + (param_num - 4 - 1) * 4)

			param_num += 1



		self.frame_size: int = STACK_ALIGNMENT * ((offset + STACK_ALIGNMENT - 1) // STACK_ALIGNMENT)
		self.touched: Set[str] = set()






	# if skip_loads is true, we don't bother loading the old value from the stack to the new register; the
	# assumption is that we will soon store to that register, so there's no point loading anything
	def make_available(self, var: str, skip_loads = False) -> str:
		loc = self.locations[var]

		# if the var is already in a register, use it
		if loc.have_register():
			return loc.register()

		# if we have a free register, load from memory to that register
		for (reg, cur) in self.registers.items():
			if cur == "":
				# update the register descriptor and variable location
				self.registers[reg] = var
				self.locations[var].set_register(reg)

				# do a load. stack_ofs is still valid (we can be both)
				if not skip_loads:
					self.cs.emit(f"ldr {reg}, [fp, #{loc.stack_ofs()}]")

				self.touched.add(reg)
				return reg

		# we didn't, so spill something. for now, just spill the first one.
		reg = next(iter(self.registers))
		old_var = self.registers[reg]

		# unset the current register from the loc first
		self.locations[old_var].clear_register()

		# prepare to spill
		stk_ofs = self.locations[old_var].stack_ofs()
		self.cs.emit(f"str {reg}, [fp, #{stk_ofs}]")

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
def codegen_value(cs: CodegenState, vs: VarState, operand: ir3.Value) -> Tuple[str, bool]:
	if isinstance(operand, ir3.ConstantInt):
		return f"#{operand.value}", True

	elif isinstance(operand, ir3.ConstantBool):
		return f"#{0 if not operand.value else 1}", True

	elif isinstance(operand, ir3.ConstantNull):
		return f"#0", True

	elif isinstance(operand, ir3.ConstantString):
		assert False and "not implemented"

	elif isinstance(operand, ir3.VarRef):
		return vs.make_available(operand.name), False

	else:
		assert False and "unreachable"



def codegen_binop(cs: CodegenState, vs: VarState, expr: ir3.BinaryOp, dest_reg: str):
	if expr.strs:
		# TODO: string concatenation
		assert False and "not implemented"

	elif expr.op == "/":
		# TODO: long division routine
		assert False and "not implemented"




	lhs, lc = codegen_value(cs, vs, expr.lhs)
	rhs, rc = codegen_value(cs, vs, expr.rhs)

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

	else:
		print("not implemented")




def codegen_expr(cs: CodegenState, vs: VarState, expr: ir3.Expr, dest_reg: str):
	if isinstance(expr, ir3.BinaryOp):
		codegen_binop(cs, vs, expr, dest_reg)

	elif isinstance(expr, ir3.ValueExpr):
		# we might potentially want to abstract this out, but for now idgaf
		operand, _ = codegen_value(cs, vs, expr.value)
		cs.emit(f"mov {dest_reg}, {operand}")


	else:
		print("not implemented")




def codegen_assign(cs: CodegenState, vs: VarState, assign: ir3.AssignOp):
	dest_reg = vs.make_available(assign.lhs, skip_loads=True)
	codegen_expr(cs, vs, assign.rhs, dest_reg)




def codegen_return(cs: CodegenState, vs: VarState, stmt: ir3.ReturnStmt):
	if stmt.value is not None:
		value, _ = codegen_value(cs, vs, stmt.value)
		cs.emit(f"mov a1, {value}")

	cs.emit(f"b {cs.prologue_label}")




def codegen_stmt(cs: CodegenState, vs: VarState, stmt: ir3.Stmt):
	cs.comment(str(stmt))
	if isinstance(stmt, ir3.AssignOp):
		codegen_assign(cs, vs, stmt)

	elif isinstance(stmt, ir3.ReturnStmt):
		codegen_return(cs, vs, stmt)

	else:
		print("not implemented")



def codegen_method(cs: CodegenState, method: ir3.FuncDefn):
	vs = VarState(cs, method.vars, method.params)

	# time to start emitting code...
	cs.emit(f".global {method.name}", indent = 0)
	cs.emit(f".type {method.name}, %function", indent = 0)
	cs.emit(f"{method.name}:", indent = 0)

	# start sending stuff to the gulag, from which we will later rescue them
	cs.begin_scope()

	# the way we handle returns (which isn't a good way i admit) is to just set the return
	# value in a1 (if any), then branch to the epilogue. so, emit a label here:
	cs.set_prologue(f".{method.name}_epilogue")

	for block in method.blocks:
		block_name = block.name

		# the original point of prepending '.' was the hope that they would be local
		# labels like nasm or something. unfortunately that isn't the case.
		if block_name[0] == '.':
			block_name = block_name[1:]

		block_name = f".{method.name}_{block_name}"

		cs.emit(f"{block_name}:", indent = 0)
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

	return cs.lines

