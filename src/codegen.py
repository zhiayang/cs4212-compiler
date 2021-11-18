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


# returns (string, is_constant, type)
def codegen_value(cs: CodegenState, fs: FuncState, val: ir3.Value) -> cgarm.Operand:
	if isinstance(val, ir3.VarRef):
		return fs.get_location(val.name).register()

	elif isinstance(val, ir3.ConstantInt):
		return cgarm.Constant(val.value)

	if isinstance(val, ir3.ConstantBool):
		return cgarm.Constant(0 if not val.value else 1)

	elif isinstance(val, ir3.ConstantNull):
		return cgarm.Constant(0)

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



def codegen_binop(cs: CodegenState, fs: FuncState, expr: ir3.BinaryOp, dest_reg: cgarm.Register):

	if expr.op == "s+":
		# TODO: string concatenation
		cs.comment("NOT IMPLEMENTED (string concat)")
		return

	elif expr.op == "/":
		# TODO: long division routine
		cs.comment("NOT IMPLEMENTED (division)")
		return


	lhs = codegen_value(cs, fs, expr.lhs)
	rhs = codegen_value(cs, fs, expr.rhs)

	# turns out all of these need unique paths ><
	if expr.op == "+":
		fs.emit(cgarm.add(dest_reg, lhs, rhs))

	elif expr.op == "-":
		fs.emit(cgarm.sub(dest_reg, lhs, rhs))

	elif expr.op == "*":
		fs.emit(cgarm.mul(dest_reg, lhs, rhs))

	elif expr.op in ["==", "!=", "<=", ">=", "<", ">"]:
		instr_map   = {"==": "eq", "!=": "ne", "<=": "le", ">=": "ge", "<": "lt", ">": "gt"}
		flipped_map = {"eq": "ne", "ne": "eq", "le": "gt", "ge": "lt", "lt": "ge", "gt": "le"}

		cond = cgarm.Cond.from_operator(expr.op)
		if lhs.is_constant():
			cond = cond.invert()
			lhs, rhs = rhs, lhs

		fs.emit(cgarm.cmp(lhs, rhs))
		fs.emit(cgarm.mov_cond(dest_reg, cgarm.Constant(1), cond))
		fs.emit(cgarm.mov_cond(dest_reg, cgarm.Constant(0), cond.invert()))

	else:
		cs.comment(f"NOT IMPLEMENTED (binop '{expr.op}')")


def codegen_unaryop(cs: CodegenState, fs: FuncState, expr: ir3.UnaryOp, dest_reg: cgarm.Register):
	oper = codegen_value(cs, fs, expr.expr)

	if expr.op == "-":
		fs.emit(cgarm.rsb(dest_reg, oper, cgarm.Constant(0)))

	elif expr.op == "!":
		# 1 - x works as long as 0 < x < 1 (which should hold...)
		fs.emit(cgarm.rsb(dest_reg, oper, cgarm.Constant(1)))

	else:
		raise CGException(f"unsupported unary op '{expr.op}'")



def codegen_dotop(cs: CodegenState, fs: FuncState, dot: ir3.DotOp, dest_reg: cgarm.Register, _: int):
	ptr = fs.get_location(dot.lhs).register()
	layout = cs.get_class_layout(fs.get_type(dot.lhs))
	offset = layout.field_offset(dot.rhs)

	if layout.field_size(dot.rhs) == 1:
		fs.emit(cgarm.load_byte(dest_reg, cgarm.Memory(ptr, offset)))
	else:
		fs.emit(cgarm.load(dest_reg, cgarm.Memory(ptr, offset)))


def codegen_expr(cs: CodegenState, fs: FuncState, expr: ir3.Expr, dest_reg: cgarm.Register, stmt_id: int):
	if isinstance(expr, ir3.BinaryOp):
		codegen_binop(cs, fs, expr, dest_reg)

	elif isinstance(expr, ir3.UnaryOp):
		codegen_unaryop(cs, fs, expr, dest_reg)

	elif isinstance(expr, ir3.ValueExpr):
		# we might potentially want to abstract this out, but for now idgaf
		operand = codegen_value(cs, fs, expr.value)
		fs.emit(cgarm.mov(dest_reg, operand))

	elif isinstance(expr, ir3.FnCallExpr):
		codegen_call(cs, fs, expr.call, dest_reg, stmt_id)

	elif isinstance(expr, ir3.DotOp):
		codegen_dotop(cs, fs, expr, dest_reg, stmt_id)

	elif isinstance(expr, ir3.NewOp):
		cls_size = cs.get_class_layout(expr.cls).size()
		assert cls_size > 0

		spills, stack_adjust = pre_function_call(cs, fs, stmt_id, dest_reg = dest_reg)

		fs.emit(cgarm.mov(cgarm.A1, cgarm.Constant(1)))
		fs.emit(cgarm.mov(cgarm.A2, cgarm.Constant(cls_size)))
		fs.emit(cgarm.call("calloc(PLT)"))

		# move the return value from A1 to the correct destination
		fs.emit(cgarm.mov(dest_reg, cgarm.A1))

		post_function_call(cs, fs, spills, stack_adjust)

	else:
		cs.comment(f"NOT IMPLEMENTED (expression)")




def codegen_assign(cs: CodegenState, fs: FuncState, assign: ir3.AssignOp):
	# if this had no location, then it must be an unused variable, which is fine.
	# this is only valid in assignments, since any use of it elsewhere would
	# obviously necessitate that it is used.

	if not (loc := fs.get_location(assign.lhs)).have_register():
		return

	codegen_expr(cs, fs, assign.rhs, loc.register(), assign.id)




def codegen_return(cs: CodegenState, fs: FuncState, stmt: ir3.ReturnStmt):
	if stmt.value is not None:
		value = codegen_value(cs, fs, stmt.value)
		fs.emit(cgarm.mov(cgarm.A1, value))

	fs.branch_to_exit()


def codegen_uncond_branch(cs: CodegenState, fs: FuncState, ubr: ir3.Branch):
	fs.emit(cgarm.branch(fs.mangle_label(ubr.label)))


def codegen_cond_branch(cs: CodegenState, fs: FuncState, cbr: ir3.CondBranch):
	# we should have lowered all conditions to be values (bringing the cond outside the loop).
	assert isinstance(cbr.cond, ir3.Value)
	assert get_value_type(cs, fs, cbr.cond) == "Bool"

	target = fs.mangle_label(cbr.label)

	if isinstance(cbr.cond, ir3.ConstantBool):
		if cbr.cond.value:
			fs.emit(cgarm.branch(target))
		else:
			cs.comment("constant branch eliminated; fallthrough")
			pass
	else:
		value = codegen_value(cs, fs, cbr.cond)
		fs.emit(cgarm.cmp(value, cgarm.Constant(0)))
		fs.emit(cgarm.branch_cond(target, cgarm.Cond.NE))


def pre_function_call(cs: CodegenState, fs: FuncState, stmt_id: int,
	dest_reg: Optional[cgarm.Register] = None) -> Tuple[List[cgarm.Register], int]:
	# for each of a1-a4, if there is some value in there, we need to save/restore across
	# the call boundary. this also acts as a spill for those values, so we don't need to
	# handle spilling separately.
	saves: List[cgarm.Register] = []
	for r in ["a1", "a2", "a3", "a4"]:
		if fs.is_register_live(r, stmt_id):
			saves.append(cgarm.Register(r))

	# ... if the destination of the call is one of these clobbered registers,
	# then don't even bother saving it.
	if dest_reg is not None and dest_reg in saves:
		saves.remove(dest_reg)

	if (fs.current_stack_offset() + 4 * len(saves)) % STACK_ALIGNMENT == 0:
		stack_adjust = 0

	else:
		fs.stack_push_32n(1).annotate("align adjustment")
		stack_adjust = 1


	if len(saves) > 0:
		fs.emit(cgarm.store_multiple(cgarm.SP.post_incr(), saves)).annotate("caller-save")
		fs.stack_extra_32n(len(saves))

	return saves, stack_adjust


def post_function_call(cs: CodegenState, fs: FuncState, saves: List[cgarm.Register], stack_adjust: int) -> None:

	# now, restore a1-a4 (if we spilled them)
	if len(saves) > 0:
		fs.emit(cgarm.load_multiple(cgarm.SP.post_incr(), saves)).annotate("caller-restore")
		fs.stack_extra_32n(-1 * len(saves))

	if stack_adjust > 0:
		fs.stack_pop_32n(stack_adjust).annotate("align adjustment")




def codegen_println(cs: CodegenState, fs: FuncState, stmt: ir3.PrintLnCall):
	value = codegen_value(cs, fs, stmt.value)
	ty = get_value_type(cs, fs, stmt.value)

	saves, stack_adjust = pre_function_call(cs, fs, stmt.id)

	# strings are always in registers
	if ty == "String":
		fs.emit(cgarm.mov(cgarm.A1, value))

		# for strings specifically, increment by 4 to skip the length. the value is a pointer anyway.
		fs.emit(cgarm.add(cgarm.A1, cgarm.A1, cgarm.Constant(4)))
		fs.emit(cgarm.call("puts(PLT)"))

	elif ty == "Int":
		fs.emit(cgarm.load_label(cgarm.A1, cs.add_string("%d\n") + "_raw"))
		fs.emit(cgarm.mov(cgarm.A2, value))
		fs.emit(cgarm.call("printf(PLT)"))

	elif ty == "Bool":
		# update the condition flags here, so that we can elide an additional 'cmp a1, #0'
		fs.emit(cgarm.mov_s(cgarm.A1, value))

		# fs.emit(cgarm.mov(cgarm.A1, value))
		# fs.emit(cgarm.cmp(cgarm.A1, cgarm.Constant(0)))
		fs.emit(cgarm.load_label(cgarm.A1, cs.add_string("false") + "_raw").conditional(cgarm.Cond.EQ))
		fs.emit(cgarm.load_label(cgarm.A1, cs.add_string("true") + "_raw").conditional(cgarm.Cond.NE))
		fs.emit(cgarm.call("puts(PLT)"))

	elif ty == "$NullObject":
		fs.emit(cgarm.load_label(cgarm.A1, cs.add_string("null") + "_raw"))
		fs.emit(cgarm.call("puts(PLT)"))

	else:
		assert False and f"unknown type {ty}"

	post_function_call(cs, fs, saves, stack_adjust)


def codegen_call(cs: CodegenState, fs: FuncState, call: ir3.FnCall, dest_reg: cgarm.Register, stmt_id: int):
	# if the number of arguments is > 4, then we set up the stack first; this
	# is so we can just use a1 as a scratch register

	saves, stack_adjust = pre_function_call(cs, fs, stmt_id, dest_reg = dest_reg)

	if len(call.args) > 4:
		# to match the C calling convention, stack arguments go right-to-left.
		stack_args = reversed(call.args[4:])

		for i, arg in enumerate(stack_args):
			# just always use a1 as a hint, since it's bound to get spilled anyway
			# note the stack offset is always -4, since we do the post increment
			val = codegen_value(cs, fs, arg)
			if val.is_constant():
				fs.emit(cgarm.mov(cgarm.A1, val))
				fs.stack_push(cgarm.A1)

			else:
				assert val.is_register()
				fs.stack_push(cast(cgarm.Register, val))

	for i, arg in enumerate(call.args[:4]):
		val = codegen_value(cs, fs, arg)
		fs.emit(cgarm.mov(cgarm.Register(f"a{i + 1}"), val))

	fs.emit(cgarm.call(call.name))

	# after the call, we need to increment the stack pointer by however many
	# extra arguments we passed.
	if len(call.args) > 4:
		fs.stack_pop_32n(len(call.args) - 4)

	# move the return value into place.
	fs.emit(cgarm.mov(dest_reg, cgarm.A1))

	post_function_call(cs, fs, saves, stack_adjust)




def codegen_storefield(cs: CodegenState, fs: FuncState, store: cgpseudo.StoreField):
	ptr = fs.get_location(store.ptr).register()
	layout = cs.get_class_layout(fs.get_type(store.ptr))
	offset = layout.field_offset(store.field)

	value = fs.get_location(store.rhs).register()

	if store.type == "Bool":
		fs.emit(cgarm.store_byte(value, cgarm.Memory(ptr, offset)))
	else:
		fs.emit(cgarm.store(value, cgarm.Memory(ptr, offset)))




def codegen_stmt(cs: CodegenState, fs: FuncState, stmt: ir3.Stmt):
	# a little janky, but i think this should work.
	fs.annotate_next(str(stmt))

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
		codegen_call(cs, fs, stmt.call, cgarm.A1, stmt.id)

	elif isinstance(stmt, cgpseudo.AssignConstInt) or isinstance(stmt, cgpseudo.AssignConstString):
		foo: Union[cgpseudo.AssignConstInt, cgpseudo.AssignConstString] = stmt
		dest_reg = fs.get_location(foo.lhs).register()

		if isinstance(foo, cgpseudo.AssignConstInt):
			fs.emit(cgarm.mov(dest_reg, cgarm.Constant(foo.rhs)))
		else:
			fs.emit(cgarm.load_label(dest_reg, cs.add_string(foo.rhs)))

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
	assigns, spills, reg_live_ranges = cgreg.allocate_registers(method)

	# setup the function state
	fs = FuncState(cs, method, assigns, spills, reg_live_ranges)

	# and codegen all the blocks.
	for block in method.blocks:
		fs.emit_label(block.name)
		for stmt in block.stmts:
			codegen_stmt(cs, fs, stmt)

	if options.optimisations_enabled():
		cgopt.optimise(fs)

	cs.emit_lines(fs.finalise())
	cs.emit_raw(f"\n")



















def codegen(prog: ir3.Program, flags: str) -> List[str]:
	cs = CodegenState(prog.classes)

	cs.emit_raw(f"@ jlite compiler: {flags}")
	cs.emit_raw(".text")
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
	@ we need a 'this' argument for this guy, so just allocate nothing.
	sub sp, sp, #4
	mov a1, sp

	bl main_dummy

	add sp, sp, #4

	@ set the return code to 0
	mov a1, #0
	ldr pc, [sp], #4
""")


	cs.emit_raw(".data")
	for string, id in cs.strings.items():
		cs.emit_raw(f".string{id}:")
		cs.emit_raw(f"    .word {len(string)}")
		cs.emit_raw(f".string{id}_raw:")
		cs.emit_raw(f'    .asciz "{escape_string(string)}"')
		cs.comment()


	return cs.lines

