#!/usr/bin/env python

from __future__ import annotations
from typing import *
from copy import *

from . import ir3
from . import cgreg
from . import cgpseudo
from . import cgannotate

from .util import Location, TCException, CGException, StringView, print_warning, escape_string
from .cgstate import *

import math



# returns (string, is_constant, type)
def codegen_value(cs: CodegenState, fs: FuncState, val: ir3.Value) -> Tuple[str, bool]:
	if isinstance(val, ir3.VarRef):
		return fs.get_location(val.name).register(), False

	elif isinstance(val, ir3.ConstantInt):
		return f"#{val.value}", True

	if isinstance(val, ir3.ConstantBool):
		return f"#{0 if not val.value else 1}", True

	elif isinstance(val, ir3.ConstantNull):
		return f"#0", True

	assert False and "unreachable"


def get_value_type(cs: CodegenState, fs: FuncState, val: ir3.Value) -> str:
	if isinstance(val, ir3.VarRef):
		return fs.get_type(val.name)

	elif isinstance(val, ir3.ConstantInt):
		return "Int"

	if isinstance(val, ir3.ConstantBool):
		return "Bool"

	elif isinstance(val, ir3.ConstantNull):
		return "$NullObject"

	assert False and "unreachable"



def codegen_binop(cs: CodegenState, fs: FuncState, expr: ir3.BinaryOp, dest_reg: str):

	if expr.op == "s+":
		# TODO: string concatenation
		cs.comment("NOT IMPLEMENTED (string concat)")
		return

	elif expr.op == "/":
		# TODO: long division routine
		cs.comment("NOT IMPLEMENTED (division)")
		return


	lhs, lc = codegen_value(cs, fs, expr.lhs)
	rhs, rc = codegen_value(cs, fs, expr.rhs)

	if lc and rc:
		raise TCException(expr.loc, "somehow, constant folding failed")

	# turns out all of these need unique paths ><
	if expr.op == "+":
		if lc:
			lhs, rhs = rhs, lhs

		cs.emit_raw(f"add {dest_reg}, {lhs}, {rhs}")

	elif expr.op == "-":
		flip = False
		if lc:
			lhs, rhs = rhs, lhs
			flip = True

		cs.emit_raw(f"{'rsb' if flip else 'sub'} {dest_reg}, {lhs}, {rhs}")

	elif expr.op == "*":
		assert (not lc) and (not rc)
		cs.emit_raw(f"mul {dest_reg}, {lhs}, {rhs}")

	elif expr.op in ["==", "!=", "<=", ">=", "<", ">"]:
		instr_map   = {"==": "eq", "!=": "ne", "<=": "le", ">=": "ge", "<": "lt", ">": "gt"}
		flipped_map = {"eq": "ne", "ne": "eq", "le": "gt", "ge": "lt", "lt": "ge", "gt": "le"}

		cond = instr_map[expr.op]
		if lc or rc:
			# keep the constant on the right i guess
			if lc:
				lhs, rhs = rhs, lhs
				cond = flipped_map[cond]

		cs.emit_raw(f"cmp {lhs}, {rhs}")
		cs.emit_raw(f"mov{cond} {dest_reg}, #1")
		cs.emit_raw(f"mov{flipped_map[cond]} {dest_reg}, #0")

	else:
		cs.comment(f"NOT IMPLEMENTED (binop '{expr.op}')")


def codegen_unaryop(cs: CodegenState, fs: FuncState, expr: ir3.UnaryOp, dest_reg: str):
	value, const = codegen_value(cs, fs, expr.expr)
	assert not const

	if expr.op == "-":
		cs.emit_raw(f"rsb {dest_reg}, {value}, #0")

	elif expr.op == "!":
		# 1 - x works as long as 0 < x < 1 (which should hold...)
		cs.emit_raw(f"rsb {dest_reg}, {value}, #1")

	else:
		raise CGException(f"unsupported unary op '{expr.op}'")



def codegen_dotop(cs: CodegenState, fs: FuncState, dot: ir3.DotOp, dest_reg: str, stmt_id: int):
	ptr = fs.get_location(dot.lhs).register()
	layout = cs.get_class_layout(fs.get_type(dot.lhs))
	offset = layout.field_offset(dot.rhs)

	if layout.field_size(dot.rhs) == 1:
		cs.emit_raw(f"ldrb {dest_reg}, [{ptr}, #{offset}]")
	else:
		cs.emit_raw(f"ldr {dest_reg}, [{ptr}, #{offset}]")




def codegen_gep(cs: CodegenState, fs: FuncState, expr: cgpseudo.GetElementPtr, dest_reg: str, stmt_id: int):
	ptr = fs.get_location(expr.ptr).register()
	layout = cs.get_class_layout(fs.get_type(expr.ptr))

	offset = layout.field_offset(expr.field)
	cs.emit_raw(f"add {dest_reg}, {ptr}, #{offset}")



def codegen_expr(cs: CodegenState, fs: FuncState, expr: ir3.Expr, dest_reg: str, stmt_id: int):
	if isinstance(expr, ir3.BinaryOp):
		codegen_binop(cs, fs, expr, dest_reg)

	elif isinstance(expr, ir3.UnaryOp):
		codegen_unaryop(cs, fs, expr, dest_reg)

	elif isinstance(expr, ir3.ValueExpr):
		# we might potentially want to abstract this out, but for now idgaf
		operand, _ = codegen_value(cs, fs, expr.value)
		cs.emit_raw(f"mov {dest_reg}, {operand}")

	elif isinstance(expr, ir3.FnCallExpr):
		codegen_call(cs, fs, expr.call, dest_reg, stmt_id)

	elif isinstance(expr, ir3.DotOp):
		codegen_dotop(cs, fs, expr, dest_reg, stmt_id)

	elif isinstance(expr, ir3.NewOp):
		cls_size = cs.get_class_layout(expr.cls).size()
		assert cls_size > 0

		spills, stack_adjust = pre_function_call(cs, fs, stmt_id)

		cs.emit_raw(f"mov a1, #1")
		cs.emit_raw(f"ldr a2, =#{cls_size}")    # note: rely on the assembler to optimise this away
		cs.emit_raw(f"bl calloc(PLT)")

		if dest_reg != "a1":
			cs.emit_raw(f"mov {dest_reg}, a1")

		post_function_call(cs, fs, spills, stack_adjust)

	elif isinstance(expr, cgpseudo.GetElementPtr):
		codegen_gep(cs, fs, expr, dest_reg, stmt_id)

	else:
		cs.comment(f"NOT IMPLEMENTED (expression)")




def codegen_assign(cs: CodegenState, fs: FuncState, assign: ir3.AssignOp):
	dest_reg = fs.get_location(assign.lhs).register()
	codegen_expr(cs, fs, assign.rhs, dest_reg, assign.id)




def codegen_return(cs: CodegenState, fs: FuncState, stmt: ir3.ReturnStmt):
	if stmt.value is not None:
		# it actually doesn't matter what register this even is.
		value, _ = codegen_value(cs, fs, stmt.value)
		if value != "a1":
			cs.emit_raw(f"mov a1, {value}")

	cs.emit_raw(f"b {cs.epilogue_label}")



def codegen_uncond_branch(cs: CodegenState, fs: FuncState, ubr: ir3.Branch):
	cs.emit_raw(f"b {cs.mangle_label(ubr.label)}")


def codegen_cond_branch(cs: CodegenState, fs: FuncState, cbr: ir3.CondBranch):
	# we should have lowered all conditions to be values (bringing the cond outside the loop).
	assert isinstance(cbr.cond, ir3.Value)
	assert get_value_type(cs, fs, cbr.cond) == "Bool"

	target = cs.mangle_label(cbr.label)

	if isinstance(cbr.cond, ir3.ConstantBool):
		if cbr.cond.value:
			cs.emit_raw(f"b {target}")
		else:
			cs.comment("constant branch eliminated; fallthrough")
			pass
	else:
		value, _ = codegen_value(cs, fs, cbr.cond)
		cs.emit_raw(f"cmp {value}, #0")
		cs.emit_raw(f"bne {target}")


def pre_function_call(cs: CodegenState, fs: FuncState, stmt_id: int) -> Tuple[List[str], int]:
	# for each of a1-a4, if there is some value in there, we need to save/restore across
	# the call boundary. this also acts as a spill for those values, so we don't need to
	# handle spilling separately.
	spills: List[str] = []
	for r in ["a1", "a2", "a3", "a4"]:
		if fs.is_register_live(r, stmt_id):
			spills.append(r)

	if len(spills) > 0:
		cs.emit_raw(f"stmfd sp!, {{{', '.join(spills)}}}")
		fs.stack_extra_32n(len(spills))

	if fs.current_stack_offset() % STACK_ALIGNMENT == 0:
		stack_adjust = 0
	else:
		fs.stack_push_32n(1)
		cs.comment_line("align adjustment")
		stack_adjust = 1

	return spills, stack_adjust


def post_function_call(cs: CodegenState, fs: FuncState, spills: List[str], stack_adjust: int) -> None:
	# now, restore a1-a4 (if we spilled them)
	if len(spills) > 0:
		cs.emit_raw(f"ldmfd sp!, {{{', '.join(spills)}}}")
		fs.stack_extra_32n(-1 * len(spills))

	if stack_adjust > 0:
		fs.stack_pop_32n(stack_adjust)
		cs.comment_line("align adjustment")


def codegen_println(cs: CodegenState, fs: FuncState, stmt: ir3.PrintLnCall):
	value, _ = codegen_value(cs, fs, stmt.value)
	ty = get_value_type(cs, fs, stmt.value)

	spills, stack_adjust = pre_function_call(cs, fs, stmt.id)

	# strings are always in registers
	if ty == "String":
		cs.emit_raw(f"mov a1, {value}")

		# for strings specifically, increment by 4 to skip the length. the value is a pointer anyway.
		cs.emit_raw(f"add a1, a1, #4")
		cs.emit_raw(f"bl puts(PLT)")

	elif ty == "Int":
		asdf = cs.add_string("%d\n")
		cs.emit_raw(f"ldr a1, ={asdf}_raw")
		cs.emit_raw(f"mov a2, {value}")
		cs.emit_raw(f"bl printf(PLT)")

	elif ty == "Bool":
		cs.emit_raw(f"mov a1, {value}")
		cs.emit_raw(f"cmp a1, #0")
		cs.emit_raw(f"ldreq a1, ={cs.add_string('false')}_raw")
		cs.emit_raw(f"ldrne a1, ={cs.add_string('true')}_raw")
		cs.emit_raw(f"bl puts(PLT)")

	elif ty == "$NullObject":
		cs.emit_raw(f"ldr a1, ={cs.add_string('null')}_raw")
		cs.emit_raw(f"bl puts(PLT)")

	else:
		assert False and f"unknown type {ty}"

	post_function_call(cs, fs, spills, stack_adjust)


def codegen_call(cs: CodegenState, fs: FuncState, call: ir3.FnCall, dest_reg: str, stmt_id: int):
	# if the number of arguments is > 4, then we set up the stack first; this
	# is so we can just use a1 as a scratch register

	spills, stack_adjust = pre_function_call(cs, fs, stmt_id)

	if len(call.args) > 4:
		# to match the C calling convention, stack arguments go right-to-left.
		stack_args = reversed(call.args[4:])

		for i, arg in enumerate(stack_args):
			# just always use a1 as a hint, since it's bound to get spilled anyway
			# note the stack offset is always -4, since we do the post increment
			val, const = codegen_value(cs, fs, arg)
			if const:
				cs.emit_raw(f"mov a1, {val}")

			fs.stack_push(val)

	for i, arg in enumerate(call.args[:4]):
		reg = f"a{i + 1}"
		val, _ = codegen_value(cs, fs, arg)

		if val != reg:
			cs.emit_raw(f"mov {reg}, {val}")

	cs.emit_raw(f"bl {call.name}")

	# after the call, we need to increment the stack pointer by however many
	# extra arguments we passed.
	if len(call.args) > 4:
		fs.stack_pop_32n(len(call.args) - 4)

	if dest_reg != "" and dest_reg != "a1":
		cs.emit_raw(f"mov {dest_reg}, a1")

	post_function_call(cs, fs, spills, stack_adjust)


def codegen_storefield(cs: CodegenState, fs: FuncState, store: cgpseudo.StoreField):
	ptr = fs.get_location(store.ptr).register()
	value, _ = codegen_value(cs, fs, store.value)

	if store.type == "Bool":
		cs.emit_raw(f"strb {value}, [{ptr}]")
	else:
		cs.emit_raw(f"str {value}, [{ptr}]")





def codegen_stmt(cs: CodegenState, fs: FuncState, stmt: ir3.Stmt):
	cs.comment(str(stmt))
	if isinstance(stmt, ir3.AssignOp):
		codegen_assign(cs, fs, stmt)

	elif isinstance(stmt, ir3.ReturnStmt):
		codegen_return(cs, fs, stmt)

	elif isinstance(stmt, ir3.PrintLnCall):
		codegen_println(cs, fs, stmt)

	elif isinstance(stmt, ir3.Branch):
		codegen_uncond_branch(cs, fs, stmt)

	elif isinstance(stmt, ir3.CondBranch):
		codegen_cond_branch(cs, fs, stmt)

	elif isinstance(stmt, ir3.FnCallStmt):
		codegen_call(cs, fs, stmt.call, "", stmt.id)

	elif isinstance(stmt, cgpseudo.AssignConstInt) or isinstance(stmt, cgpseudo.AssignConstString):
		foo: Union[cgpseudo.AssignConstInt, cgpseudo.AssignConstString] = stmt
		dest_reg = fs.get_location(foo.lhs).register()

		if isinstance(foo, cgpseudo.AssignConstInt):
			cs.emit_raw(f"ldr {dest_reg}, =#{foo.rhs}")
		else:
			cs.emit_raw(f"ldr {dest_reg}, ={cs.add_string(foo.rhs)}")

	elif isinstance(stmt, cgpseudo.SpillVariable):
		fs.spill_variable(stmt.var)

	elif isinstance(stmt, cgpseudo.RestoreVariable):
		fs.restore_variable(stmt.var)

	elif isinstance(stmt, cgpseudo.StoreField):
		codegen_storefield(cs, fs, stmt)

	elif isinstance(stmt, cgpseudo.DummyStmt):
		pass

	else:
		cs.comment("NOT IMPLEMENTED")





def codegen_method(cs: CodegenState, method: ir3.FuncDefn):
	cs.set_current_method(method)

	# time to start emitting code...
	cs.emit_raw(f".global {method.name}", indent = 0)
	cs.emit_raw(f".type {method.name}, %function", indent = 0)
	cs.emit_raw(f"{method.name}:", indent = 0)

	assigns, spills, reg_live_ranges = cgreg.allocate_registers(method)

	annot_assigns, annot_spills = cgannotate.annotate_reg_allocs(assigns, spills)

	for s in annot_spills:
		cs.comment(s)

	for a in annot_assigns:
		cs.comment(a)


	# start sending stuff to the gulag, from which we will later rescue them
	cs.begin_scope()
	fs = FuncState(cs, method.vars, method.params, assigns, spills, reg_live_ranges)

	# the way we handle returns (which isn't a good way i admit) is to just set the return
	# value in a1 (if any), then branch to the epilogue. so, emit a label here:
	cs.set_epilogue(f".{method.name}_epilogue")

	for block in method.blocks:
		cs.emit_raw(f"{cs.mangle_label(block.name)}:", indent = 0)
		for stmt in block.stmts:
			codegen_stmt(cs, fs, stmt)

	# rescue the stmts we put in the gulag
	fn_stmts = cs.get_scoped()
	cs.end_scope()

	# now that we know which registers were used, we can do the appropriate save/restore.
	# at this point the actual body has not been emitted (it's in `fn_stmts`).
	fs.emit_prologue(cs)

	cs.emit_lines(fn_stmts)

	fs.emit_epilogue(cs)
	cs.emit_raw(f"\n")



















def codegen(prog: ir3.Program, opt: bool) -> List[str]:
	cs = CodegenState(opt, prog.classes)

	cs.emit_raw(".text", indent = 0)
	for method in prog.funcs:
		if method.name == "main":
			method.name = "main_dummy"

		codegen_method(cs, method)

	# insert code to call main_dummy from the "real" main that handles the
	# return value and stuff.
	cs.emit_raw("""
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


	cs.emit_raw(".data", indent = 0)
	for string, id in cs.strings.items():
		cs.emit_raw(f".string{id}:", indent = 0)
		cs.emit_raw(f".word {len(string)}")
		cs.emit_raw(f".string{id}_raw:", indent = 0)
		cs.emit_raw(f'.asciz "{escape_string(string)}"')
		cs.comment()


	return cs.lines

