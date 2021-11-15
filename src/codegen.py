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
	def __init__(self, cs: CodegenState, vars: List[ir3.VarDecl], params: List[ir3.VarDecl]) -> None:

		self.cs = cs

		offset: int = 0

		self.locations: Dict[str, VarLoc] = dict()
		self.var_types: Dict[str, str] = dict()
		self.locked_regs: Set[str] = set()

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
				ploc.set_stack(-offset)

				offset += POINTER_SIZE

			else:
				# these arguments are passed on the stack. these are positive offsets from bp,
				# since they are "above" the current stack frame.
				ploc.set_stack(8 + (param_num - 4 - 1) * 4)
				offset += POINTER_SIZE


			self.locations[param.name] = ploc
			self.var_types[param.name] = param.type

			param_num += 1


		self.frame_size: int = STACK_ALIGNMENT * ((offset + STACK_ALIGNMENT - 1) // STACK_ALIGNMENT)
		self.touched: Set[str] = set()

	# locking a register ensures that it cannot be spilled until it is unlocked. this prevents
	# the stupid case of spilling an operand to load another operand for the same instruction.
	def lock_register(self, reg: str) -> None:
		self.locked_regs.add(reg)

	def unlock_register(self, reg: str) -> None:
		if reg in self.locked_regs:
			self.locked_regs.remove(reg)

	def unlock_all(self) -> None:
		self.locked_regs = set()

	def spill_register(self, reg: str):
		old_var = self.registers[reg]
		if old_var is not None and old_var != "" and old_var != "$scratch":
			# unset the current register from the loc first
			# print(f"old_var = {old_var}")
			self.locations[old_var].clear_register()

			# do the spill
			stk_ofs = self.locations[old_var].stack_ofs()
			self.cs.emit(f"str {reg}, [fp, #{stk_ofs}]")
			self.cs.comment_line(f"spilling '{old_var}'")


	def find_free_register(self) -> Optional[str]:
		for (reg, cur) in self.registers.items():
			if cur == "":
				return reg
		return None

	def get_register_to_spill(self) -> str:
		for k, v in self.registers.items():
			if v == "$scratch" and k not in self.locked_regs:
				return k

		# otherwise just get any unlocked register for now.
		for reg in self.registers:
			if reg not in self.locked_regs:
				return reg

		assert False and "ran out of registers!"


	def scratch_register(self) -> str:
		free_reg = self.find_free_register()
		if free_reg is not None:
			self.cs.comment_line(f"scratch = {free_reg}")
			return free_reg

		spill = self.get_register_to_spill()
		self.spill_register(spill)

		# TODO: use this to prefer spilling scratch registers. anyway there
		# shouldn't be too many of these.
		self.registers[spill] = "$scratch"
		return spill



	# if skip_loads is true, we don't bother loading the old value from the stack to the new register; the
	# assumption is that we will soon store to that register, so there's no point loading anything
	def make_available(self, var: str, reg_hint: str = "", skip_loads = False) -> str:
		loc = self.locations[var]

		# if the var is already in a register, use it
		if loc.have_register():
			# note that we don't use the provided register here; it's just a suggestion
			return loc.register()

		# the variable was not in a register, but we have a register specified; in this
		# case, load directly there (assuming that whoever called this has performed the necessary spillage)
		if reg_hint != "":
			self.registers[reg_hint] = var
			self.locations[var].set_register(reg_hint)

			if not skip_loads:
				self.cs.emit(f"ldr {reg_hint}, [fp, #{loc.stack_ofs()}]")
				self.cs.comment_line(f"load '{var}'")

			self.touched.add(reg_hint)
			return reg_hint


		# if we have a free register, load from memory to that register
		free_reg = self.find_free_register()
		if free_reg is not None:
			self.registers[free_reg] = var
			self.locations[var].set_register(free_reg)

			# do a load. stack_ofs is still valid (we can be both)
			if not skip_loads:
				self.cs.emit(f"ldr {free_reg}, [fp, #{loc.stack_ofs()}]")
				self.cs.comment_line(f"load '{var}'")

			self.touched.add(free_reg)
			return free_reg

		reg = self.get_register_to_spill()
		self.spill_register(reg)
		self.cs.comment_line(f" - for '{var}'")

		# load the new value
		stk_ofs = self.locations[var].stack_ofs()
		if not skip_loads:
			self.cs.emit(f"ldr {reg}, [fp, #{stk_ofs}]")
			self.cs.comment_line(f"load(3) '{var}'")

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
			restore_str = (", ".join(restore))

		cs.emit(f"stmfd sp!, {{fp, lr}}")
		cs.emit(f"mov fp, sp")
		cs.emit(f"sub sp, sp, #{self.frame_size}")

		if restore_str != "":
			cs.emit(f"stmfd sp!, {{{restore_str}}}")

		cs.comment("prologue")
		cs.comment()

		return restore


	def emit_epilogue(self, cs: CodegenState, restore: List[str]) -> None:
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








def codegen_constant_int(cs: CodegenState, vs: VarState, val: int, must_use_reg: bool = False, reg_hint: str = "") -> str:
	if (-128 <= val <= 127) or (0 <= val <= 255):
		if must_use_reg:
			if reg_hint != "":
				reg = reg_hint
			else:
				reg = vs.scratch_register()
			cs.emit(f"mov {reg}, #{val}")
			return reg
		else:
			return f"#{val}"

	else:
		if reg_hint != "":
			reg = reg_hint
		else:
			reg = vs.scratch_register()
		cs.emit(f"ldr {reg}, =#{val}")
		return reg


# returns (string, is_constant, type)
def codegen_value(cs: CodegenState, vs: VarState, val: ir3.Value, must_use_reg: bool = False) -> Tuple[str, bool, str]:
	if isinstance(val, ir3.VarRef):
		return vs.make_available(val.name), False, vs.var_types[val.name]

	elif isinstance(val, ir3.ConstantString):
		scr = vs.scratch_register()
		cs.emit(f"ldr {scr}, ={cs.add_string(val.value)}")
		return scr, False, "String"

	elif isinstance(val, ir3.ConstantInt):
		tmp = codegen_constant_int(cs, vs, val.value, must_use_reg = must_use_reg)
		return tmp, (tmp[0] == '#'), "Int"

	elif not must_use_reg:
		if isinstance(val, ir3.ConstantBool):
			return f"#{0 if not val.value else 1}", True, "Bool"

		elif isinstance(val, ir3.ConstantNull):
			return f"#0", True, "$NullObject"
	else:
		if isinstance(val, ir3.ConstantBool):
			cs.emit(f"mov {scr}, #{0 if not val.value else 1}")
			return scr, False, "Bool"

		elif isinstance(val, ir3.ConstantNull):
			cs.emit(f"mov {scr}, #0")
			return scr, False, "$NullObject"

	assert False and "unreachable"


# this only uses the given register for constants. for values, it we just
def codegen_value_into_register(cs: CodegenState, vs: VarState, val: ir3.Value, reg: str) -> str:
	if isinstance(val, ir3.VarRef):
		return vs.make_available(val.name, reg_hint = reg)

	elif isinstance(val, ir3.ConstantString):
		cs.emit(f"ldr {reg}, ={cs.add_string(val.value)}")
		return reg

	elif isinstance(val, ir3.ConstantInt):
		return codegen_constant_int(cs, vs, val.value, must_use_reg = True, reg_hint = reg)

	elif isinstance(val, ir3.ConstantBool):
		cs.emit(f"mov {reg}, #{0 if not val.value else 1}")
		return reg

	elif isinstance(val, ir3.ConstantNull):
		cs.emit(f"mov {reg}, #0")
		return reg

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
	if not lc:
		vs.lock_register(lhs)

	rhs, rc, _ = codegen_value(cs, vs, expr.rhs)
	if not rc:
		vs.lock_register(rhs)

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

			cs.emit(f"lsl {dest_reg}, {lhs}, #{p2 - 1}")

			while mult > 0:
				cs.emit(f"add {dest_reg}, {dest_reg}, {lhs}")
				mult -= 1

			if negate:
				cs.emit(f"rsb {dest_reg}, {dest_reg}, #0")

		else:
			cs.emit(f"mul {dest_reg}, {lhs}, {rhs}")

	elif expr.op in ["==", "!=", "<=", ">=", "<", ">"]:
		instr_map   = {"==": "eq", "!=": "ne", "<=": "le", ">=": "ge", "<": "lt", ">": "gt"}
		flipped_map = {"eq": "ne", "ne": "eq", "le": "gt", "ge": "lt", "lt": "ge", "gt": "le"}

		cs.emit(f"mov {dest_reg}, #0")

		cond = instr_map[expr.op]
		if lc or rc:
			# keep the constant on the right i guess
			if lc:
				lhs, rhs = rhs, lhs
				cond = flipped_map[cond]

		cs.emit(f"cmp {lhs}, {rhs}")
		cs.emit(f"mov{instr_map[expr.op]} {dest_reg}, #1")

	else:
		cs.comment(f"NOT IMPLEMENTED (binop '{expr.op}')")

	vs.unlock_register(lhs)
	vs.unlock_register(rhs)



def codegen_expr(cs: CodegenState, vs: VarState, expr: ir3.Expr, dest_reg: str):
	if isinstance(expr, ir3.BinaryOp):
		codegen_binop(cs, vs, expr, dest_reg)

	elif isinstance(expr, ir3.ValueExpr):
		# we might potentially want to abstract this out, but for now idgaf
		operand, _, _ = codegen_value(cs, vs, expr.value)
		cs.emit(f"mov {dest_reg}, {operand}")

	elif isinstance(expr, ir3.FnCallExpr):
		codegen_call(cs, vs, expr.call)

	else:
		cs.comment(f"NOT IMPLEMENTED (expression)")




def codegen_assign(cs: CodegenState, vs: VarState, assign: ir3.AssignOp):
	dest_reg = vs.make_available(assign.lhs, skip_loads=True)
	vs.lock_register(dest_reg)

	codegen_expr(cs, vs, assign.rhs, dest_reg)

	vs.unlock_register(dest_reg)




def codegen_return(cs: CodegenState, vs: VarState, stmt: ir3.ReturnStmt):
	if stmt.value is not None:
		value = codegen_value_into_register(cs, vs, stmt.value, reg = "a1")
		if value != "a1":
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
	value, _, ty = codegen_value(cs, vs, stmt.value)

	# strings are always in registers
	if ty == "String":
		vs.spill_register("a1")
		cs.emit(f"mov a1, {value}")

		# for strings specifically, increment by 4 to skip the length. the value is a pointer anyway.
		cs.emit(f"add a1, a1, #4")
		cs.emit(f"bl puts(PLT)")
		return

	elif ty == "Int":
		vs.spill_register("a1")
		vs.spill_register("a2")

		asdf = cs.add_string("%d\n")
		cs.emit(f"ldr a1, ={asdf}")
		cs.emit(f"mov a2, {value}")
		cs.emit(f"bl printf(PLT)")

	elif ty == "Bool":
		vs.spill_register("a1")
		cs.emit(f"mov a1, {value}")
		cs.emit(f"cmp a1, #0")
		cs.emit(f"ldreq a1, ={cs.add_string('false')}")
		cs.emit(f"ldrne a1, ={cs.add_string('true')}")
		cs.emit(f"bl puts(PLT)")

	elif ty == "$NullObject":
		vs.spill_register("a1")
		cs.emit(f"ldr a1, ={cs.add_string('null')}")
		cs.emit(f"bl puts(PLT)")

	else:
		assert False and f"unknown type {ty}"


def codegen_call(cs: CodegenState, vs: VarState, call: ir3.FnCall):
	# if the number of arguments is > 4, then we set up the stack first; this
	# is so we can just use a1 as a scratch register

	spilled_a1 = False

	if len(call.args) > 4:
		# to match the C calling convention, stack arguments go right-to-left.
		stack_args = reversed(call.args[4:])

		vs.spill_register("a1")
		spilled_a1 = True

		for i, arg in enumerate(stack_args):
			# just always use a1 as a hint, since it's bound to get spilled anyway
			# note the stack offset is always -4, since we do the post increment
			val = codegen_value_into_register(cs, vs, arg, reg = "a1")
			cs.emit(f"str {val}, [sp, #-4]!")


	if len(call.args) > 3:  vs.spill_register("a4")
	if len(call.args) > 2:  vs.spill_register("a3")
	if len(call.args) > 1:  vs.spill_register("a2")
	if len(call.args) > 0 and not spilled_a1:
		vs.spill_register("a1")

	for i, arg in enumerate(call.args[:4]):
		reg = f"a{i + 1}"
		val = codegen_value_into_register(cs, vs, arg, reg = reg)
		if val != reg:
			cs.emit(f"mov {reg}, {val}")

	cs.emit(f"bl {call.name}")

	# after the call, we need to increment the stack pointer by however many
	# extra arguments we passed.
	if len(call.args) > 4:
		cs.emit(f"add sp, sp, #{4 * (len(call.args) - 4)}")







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

	elif isinstance(stmt, ir3.FnCallStmt):
		codegen_call(cs, vs, stmt.call)

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
	@ we need a 'this' argument for this guy, so just allocate
	@ nothing.

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

