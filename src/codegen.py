#!/usr/bin/env python

from __future__ import annotations
from typing import *
from copy import *

from . import ir3
from . import regalloc
from . import cgpseudo

from .util import Location, TCException, CGException, StringView, print_warning, escape_string
from .cgstate import *

import math



# returns (string, is_constant, type)
def codegen_value(cs: CodegenState, vs: VarState, val: ir3.Value) -> Tuple[str, bool]:
	if isinstance(val, ir3.VarRef):
		return vs.load_var(val.name), False

	elif isinstance(val, ir3.ConstantInt):
		return f"#{val.value}", True

	if isinstance(val, ir3.ConstantBool):
		return f"#{0 if not val.value else 1}", True

	elif isinstance(val, ir3.ConstantNull):
		return f"#0", True

	assert False and "unreachable"


def get_value_type(cs: CodegenState, vs: VarState, val: ir3.Value) -> str:
	if isinstance(val, ir3.VarRef):
		return vs.get_type(val.name)

	elif isinstance(val, ir3.ConstantInt):
		return "Int"

	if isinstance(val, ir3.ConstantBool):
		return "Bool"

	elif isinstance(val, ir3.ConstantNull):
		return "$NullObject"

	assert False and "unreachable"



def codegen_binop(cs: CodegenState, vs: VarState, expr: ir3.BinaryOp, dest_reg: str):

	if expr.op == "s+":
		# TODO: string concatenation
		cs.comment("NOT IMPLEMENTED (string concat)")
		return

	elif expr.op == "/":
		# TODO: long division routine
		cs.comment("NOT IMPLEMENTED (division)")
		return


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

		cs.emit(f"{'rsb' if flip else 'sub'} {dest_reg}, {lhs}, {rhs}")

	elif expr.op == "*":
		assert (not lc) and (not rc)
		cs.emit(f"mul {dest_reg}, {lhs}, {rhs}")

	elif expr.op in ["==", "!=", "<=", ">=", "<", ">"]:
		instr_map   = {"==": "eq", "!=": "ne", "<=": "le", ">=": "ge", "<": "lt", ">": "gt"}
		flipped_map = {"eq": "ne", "ne": "eq", "le": "gt", "ge": "lt", "lt": "ge", "gt": "le"}

		cond = instr_map[expr.op]
		if lc or rc:
			# keep the constant on the right i guess
			if lc:
				lhs, rhs = rhs, lhs
				cond = flipped_map[cond]

		cs.emit(f"cmp {lhs}, {rhs}")
		cs.emit(f"mov{cond} {dest_reg}, #1")
		cs.emit(f"mov{flipped_map[cond]} {dest_reg}, #0")

	else:
		cs.comment(f"NOT IMPLEMENTED (binop '{expr.op}')")


def codegen_unaryop(cs: CodegenState, vs: VarState, expr: ir3.UnaryOp, dest_reg: str):
	value, const = codegen_value(cs, vs, expr.expr)
	assert not const

	if expr.op == "-":
		cs.emit(f"rsb {dest_reg}, {value}, #0")

	elif expr.op == "!":
		# 1 - x works as long as 0 < x < 1 (which should hold...)
		cs.emit(f"rsb {dest_reg}, {value}, #1")

	else:
		raise CGException(f"unsupported unary op '{expr.op}'")



def codegen_dotop(cs: CodegenState, vs: VarState, dot: ir3.DotOp, dest_reg: str, stmt_id: int):
	ptr = vs.load_var(dot.lhs)
	layout = cs.get_class_layout(vs.get_type(dot.lhs))
	offset = layout.field_offset(dot.rhs)

	if layout.field_size(dot.rhs) == 1:
		cs.emit(f"ldrb {dest_reg}, [{ptr}, #{offset}]")
	else:
		cs.emit(f"ldr {dest_reg}, [{ptr}, #{offset}]")




def codegen_gep(cs: CodegenState, vs: VarState, expr: cgpseudo.GetElementPtr, dest_reg: str, stmt_id: int):
	ptr = vs.load_var(expr.ptr)
	layout = cs.get_class_layout(vs.get_type(expr.ptr))

	offset = layout.field_offset(expr.field)
	cs.emit(f"add {dest_reg}, {ptr}, #{offset}")



def codegen_expr(cs: CodegenState, vs: VarState, expr: ir3.Expr, dest_reg: str, stmt_id: int):
	if isinstance(expr, ir3.BinaryOp):
		codegen_binop(cs, vs, expr, dest_reg)

	elif isinstance(expr, ir3.UnaryOp):
		codegen_unaryop(cs, vs, expr, dest_reg)

	elif isinstance(expr, ir3.ValueExpr):
		# we might potentially want to abstract this out, but for now idgaf
		operand, _ = codegen_value(cs, vs, expr.value)
		cs.emit(f"mov {dest_reg}, {operand}")

	elif isinstance(expr, ir3.FnCallExpr):
		codegen_call(cs, vs, expr.call, dest_reg, stmt_id)

	elif isinstance(expr, ir3.DotOp):
		codegen_dotop(cs, vs, expr, dest_reg, stmt_id)

	elif isinstance(expr, ir3.NewOp):
		cls_size = cs.get_class_layout(expr.cls).size()
		assert cls_size > 0

		spills = save_arg_regs(cs, vs, stmt_id)

		cs.emit(f"mov a1, #1")
		cs.emit(f"ldr a2, =#{cls_size}")    # note: rely on the assembler to optimise this away
		cs.emit(f"bl calloc(PLT)")

		if dest_reg != "a1":
			cs.emit(f"mov {dest_reg}, a1")

		restore_arg_regs(cs, vs, spills)

	elif isinstance(expr, cgpseudo.GetElementPtr):
		codegen_gep(cs, vs, expr, dest_reg, stmt_id)

	else:
		cs.comment(f"NOT IMPLEMENTED (expression)")




def make_available(cs: CodegenState, vs: VarState, var: str) -> Tuple[VarLoc, str, bool]:
	loc = vs.get_location(var)
	if not loc.have_register():
		raise CGException(f"did not get register for '{var}'")

	spill = False
	dest_reg = loc.register()

	return loc, dest_reg, spill

def writeback_spill(cs: CodegenState, vs: VarState, spill: bool, loc: VarLoc, dest_reg: str, var: str):
	if spill and vs.is_var_used(var):
		cs.emit(f"str {dest_reg}, [fp, #{loc.stack_ofs()}]")
		cs.comment_line(f"spill/wb {var}")



def codegen_assign(cs: CodegenState, vs: VarState, assign: ir3.AssignOp):

	dest_reg = vs.make_dest_available(assign.lhs)

	codegen_expr(cs, vs, assign.rhs, dest_reg, assign.id)

	vs.writeback_dest(assign.lhs, dest_reg)




def codegen_return(cs: CodegenState, vs: VarState, stmt: ir3.ReturnStmt):
	if stmt.value is not None:
		# it actually doesn't matter what register this even is.
		value, _ = codegen_value(cs, vs, stmt.value)
		if value != "a1":
			cs.emit(f"mov a1, {value}")

	cs.emit(f"b {cs.prologue_label}")



def codegen_uncond_branch(cs: CodegenState, vs: VarState, ubr: ir3.Branch):
	cs.emit(f"b {cs.mangle_label(ubr.label)}")


def codegen_cond_branch(cs: CodegenState, vs: VarState, cbr: ir3.CondBranch):
	# we should have lowered all conditions to be values (bringing the cond outside the loop).
	assert isinstance(cbr.cond, ir3.Value)
	assert get_value_type(cs, vs, cbr.cond) == "Bool"

	target = cs.mangle_label(cbr.label)

	if isinstance(cbr.cond, ir3.ConstantBool):
		if cbr.cond.value:
			cs.emit(f"b {target}")
		else:
			cs.comment("constant branch eliminated; fallthrough")
			pass
	else:
		value, _ = codegen_value(cs, vs, cbr.cond)
		cs.emit(f"cmp {value}, #0")
		cs.emit(f"bne {target}")


def save_arg_regs(cs: CodegenState, vs: VarState, stmt_id: int) -> List[str]:
	# for each of a1-a4, if there is some value in there, we need to save/restore across
	# the call boundary. this also acts as a spill for those values, so we don't need to
	# handle spilling separately.
	spills: List[str] = []
	for r in ["a1", "a2", "a3", "a4"]:
		if vs.is_register_live(r, stmt_id):
			spills.append(r)

	if len(spills) > 0:
		cs.emit(f"stmfd sp!, {{{', '.join(spills)}}}")

	return spills

def restore_arg_regs(cs: CodegenState, vs: VarState, spills: List[str]) -> None:
	# now, restore a1-a4 (if we spilled them)
	if len(spills) > 0:
		cs.emit(f"ldmfd sp!, {{{', '.join(spills)}}}")



def codegen_println(cs: CodegenState, vs: VarState, stmt: ir3.PrintLnCall):
	value, _ = codegen_value(cs, vs, stmt.value)
	ty = get_value_type(cs, vs, stmt.value)

	spills = save_arg_regs(cs, vs, stmt.id)

	# strings are always in registers
	if ty == "String":
		cs.emit(f"mov a1, {value}")

		# for strings specifically, increment by 4 to skip the length. the value is a pointer anyway.
		cs.emit(f"add a1, a1, #4")
		cs.emit(f"bl puts(PLT)")

	elif ty == "Int":
		asdf = cs.add_string("%d\n")
		cs.emit(f"ldr a1, ={asdf}_raw")
		cs.emit(f"mov a2, {value}")
		cs.emit(f"bl printf(PLT)")

	elif ty == "Bool":
		cs.emit(f"mov a1, {value}")
		cs.emit(f"cmp a1, #0")
		cs.emit(f"ldreq a1, ={cs.add_string('false')}_raw")
		cs.emit(f"ldrne a1, ={cs.add_string('true')}_raw")
		cs.emit(f"bl puts(PLT)")

	elif ty == "$NullObject":
		cs.emit(f"ldr a1, ={cs.add_string('null')}_raw")
		cs.emit(f"bl puts(PLT)")

	else:
		assert False and f"unknown type {ty}"

	restore_arg_regs(cs, vs, spills)


def codegen_call(cs: CodegenState, vs: VarState, call: ir3.FnCall, dest_reg: str, stmt_id: int):
	# if the number of arguments is > 4, then we set up the stack first; this
	# is so we can just use a1 as a scratch register

	spills = save_arg_regs(cs, vs, stmt_id)

	if len(call.args) > 4:
		# to match the C calling convention, stack arguments go right-to-left.
		stack_args = reversed(call.args[4:])

		for i, arg in enumerate(stack_args):
			# just always use a1 as a hint, since it's bound to get spilled anyway
			# note the stack offset is always -4, since we do the post increment
			val, const = codegen_value(cs, vs, arg)
			if const:
				cs.emit(f"mov a1, {val}")

			cs.emit(f"str {val}, [sp, #-4]!")

	for i, arg in enumerate(call.args[:4]):
		reg = f"a{i + 1}"
		val, _ = codegen_value(cs, vs, arg)

		if val != reg:
			cs.emit(f"mov {reg}, {val}")

	cs.emit(f"bl {call.name}")

	# after the call, we need to increment the stack pointer by however many
	# extra arguments we passed.
	if len(call.args) > 4:
		cs.emit(f"add sp, sp, #{4 * (len(call.args) - 4)}")

	if dest_reg != "" and dest_reg != "a1":
		cs.emit(f"mov {dest_reg}, a1")

	restore_arg_regs(cs, vs, spills)


def codegen_storefield(cs: CodegenState, vs: VarState, store: cgpseudo.StoreField):
	ptr = vs.load_var(store.ptr)
	value, _ = codegen_value(cs, vs, store.value)

	if store.type == "Bool":
		cs.emit(f"strb {value}, [{ptr}]")
	else:
		cs.emit(f"str {value}, [{ptr}]")





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
		codegen_call(cs, vs, stmt.call, "", stmt.id)

	elif isinstance(stmt, cgpseudo.AssignConstInt) or isinstance(stmt, cgpseudo.AssignConstString):
		foo: Union[cgpseudo.AssignConstInt, cgpseudo.AssignConstString] = stmt
		dest_reg = vs.make_dest_available(foo.lhs)

		if isinstance(foo, cgpseudo.AssignConstInt):
			cs.emit(f"ldr {dest_reg}, =#{foo.rhs}")
		else:
			cs.emit(f"ldr {dest_reg}, ={cs.add_string(foo.rhs)}")

		vs.writeback_dest(foo.lhs, dest_reg)

	# the reason that we have to assert we have a register, even when we're spilling, is because
	# we must spill from somewhere. by the virtue of inserting these spill/reload pseudo-ops, the
	# live range of the var should have split, giving us a variable to assign it.
	elif isinstance(stmt, cgpseudo.SpillVariable):
		loc = vs.get_location(stmt.var)
		if not loc.have_register():
			raise CGException(f"no register to spill '{stmt.var}'")

		cs.emit(f"str {loc.register()}, [fp, #{loc.stack_ofs()}]")
		cs.comment_line(f"spill/wb {stmt.var}")

	elif isinstance(stmt, cgpseudo.RestoreVariable):
		loc = vs.get_location(stmt.var)
		if not loc.have_register():
			raise CGException(f"could not restore '{stmt.var}'")

		cs.emit(f"ldr {loc.register()}, [fp, #{loc.stack_ofs()}]")
		cs.comment_line(f"restore {stmt.var}")

	elif isinstance(stmt, cgpseudo.StoreField):
		codegen_storefield(cs, vs, stmt)

	elif isinstance(stmt, cgpseudo.DummyStmt):
		pass

	else:
		cs.comment("NOT IMPLEMENTED")



def codegen_method(cs: CodegenState, method: ir3.FuncDefn):
	cs.set_current_method(method)

	# time to start emitting code...
	cs.emit(f".global {method.name}", indent = 0)
	cs.emit(f".type {method.name}, %function", indent = 0)
	cs.emit(f"{method.name}:", indent = 0)

	assigns, spills, reg_live_ranges = regalloc.allocate_registers(method)
	cs.comment(f"assigns: {', '.join(map(lambda k: f'{k} = {assigns[k]}', assigns))}")
	cs.comment(f"spills:  {spills}")

	# start sending stuff to the gulag, from which we will later rescue them
	cs.begin_scope()
	vs = VarState(cs, method.vars, method.params, assigns, spills, reg_live_ranges)

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
	vs.emit_prologue(cs)

	cs.emit_lines(fn_stmts)

	vs.emit_epilogue(cs)
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
	sub sp, sp, #4
	mov a1, sp

	bl main_dummy

	add sp, sp, #4

	@ set the return code to 0
	mov a1, #0
	ldr pc, [sp], #4
""")


	cs.emit(".data", indent = 0)
	for string, id in cs.strings.items():
		cs.emit(f".string{id}:", indent = 0)
		cs.emit(f".word {len(string)}")
		cs.emit(f".string{id}_raw:", indent = 0)
		cs.emit(f'.asciz "{escape_string(string)}"')
		cs.comment()


	return cs.lines

