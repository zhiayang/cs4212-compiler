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
def get_value(cs: CodegenState, fs: FuncState, val: ir3.Value) -> cgarm.Operand:
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



def codegen_binop(cs: CodegenState, fs: FuncState, expr: ir3.BinaryOp, dest_reg: cgarm.Register, stmt_id: int):

	lhs = get_value(cs, fs, expr.lhs)
	rhs = get_value(cs, fs, expr.rhs)

	if expr.op == "s+" or expr.op == "/":
		spills, stack_adjust = pre_function_call(cs, fs, stmt_id, dest_reg)

		fs.emit(cgarm.mov(cgarm.A1, lhs))
		fs.emit(cgarm.mov(cgarm.A2, rhs))
		if expr.op == "s+":
			fs.emit(cgarm.call(cs.require_string_concat_function()))
		elif expr.op == "/":
			fs.emit(cgarm.call(cs.require_divide_function()))
		else:
			assert False and "unreachable"

		# move the return value from A1 to the correct destination
		fs.emit(cgarm.mov(dest_reg, cgarm.A1))
		post_function_call(cs, fs, spills, stack_adjust)

	# turns out all of these need unique paths ><
	elif expr.op == "+":
		fs.emit(cgarm.add(dest_reg, lhs, rhs))

	elif expr.op == "-":
		fs.emit(cgarm.sub(dest_reg, lhs, rhs))

	elif expr.op == "*":
		fs.emit(cgarm.mul(dest_reg, lhs, rhs))

	elif expr.op in ["==", "!=", "<=", ">=", "<", ">"]:
		instr_map   = {"==": "eq", "!=": "ne", "<=": "le", ">=": "ge", "<": "lt", ">": "gt"}
		flipped_map = {"eq": "ne", "ne": "eq", "le": "gt", "ge": "lt", "lt": "ge", "gt": "le"}

		lty = get_value_type(cs, fs, expr.lhs)
		rty = get_value_type(cs, fs, expr.lhs)

		# for strings, emit a call.
		if lty == "String" and rty == "String":
			spills, stack_adjust = pre_function_call(cs, fs, stmt_id, dest_reg)

			fs.emit(cgarm.mov(cgarm.A1, lhs))
			fs.emit(cgarm.mov(cgarm.A2, rhs))
			fs.emit(cgarm.call(cs.require_string_compare_function()))

			# move the return value from A1 to the correct destination
			if expr.op == "==":
				fs.emit(cgarm.mov(dest_reg, cgarm.A1))
			else:
				fs.emit(cgarm.rsb(dest_reg, cgarm.A1, cgarm.Constant(1)))

			post_function_call(cs, fs, spills, stack_adjust)

		else:
			cond = cgarm.Cond.from_operator(expr.op)
			if lhs.is_constant():
				cond = cond.invert()
				lhs, rhs = rhs, lhs

			fs.emit(cgarm.cmp(lhs, rhs))
			fs.emit(cgarm.mov_cond(dest_reg, cgarm.Constant(1), cond))
			fs.emit(cgarm.mov_cond(dest_reg, cgarm.Constant(0), cond.invert()))

	elif expr.op == "&&":
		fs.emit(cgarm.bit_and(dest_reg, lhs, rhs))

	elif expr.op == "||":
		fs.emit(cgarm.bit_or(dest_reg, lhs, rhs))

	else:
		raise CGException(f"unknown binary op '{expr.op}'")


def codegen_unaryop(cs: CodegenState, fs: FuncState, expr: ir3.UnaryOp, dest_reg: cgarm.Register):
	oper = get_value(cs, fs, expr.expr)

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
		codegen_binop(cs, fs, expr, dest_reg, stmt_id)

	elif isinstance(expr, ir3.UnaryOp):
		codegen_unaryop(cs, fs, expr, dest_reg)

	elif isinstance(expr, ir3.ValueExpr):
		# we might potentially want to abstract this out, but for now idgaf
		operand = get_value(cs, fs, expr.value)
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
		raise CGException(f"expression '{type(expr)}' not implemented")




def codegen_assign(cs: CodegenState, fs: FuncState, assign: ir3.AssignOp):
	# if this had no location, then it must be an unused variable, which is fine.
	# this is only valid in assignments, since any use of it elsewhere would
	# obviously necessitate that it is used.

	if not (loc := fs.get_location(assign.lhs)).have_register():
		return

	codegen_expr(cs, fs, assign.rhs, loc.register(), assign.id)




def codegen_return(cs: CodegenState, fs: FuncState, stmt: ir3.ReturnStmt):
	if stmt.value is not None:
		value = get_value(cs, fs, stmt.value)
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
		value = get_value(cs, fs, cbr.cond)
		fs.emit(cgarm.cmp(value, cgarm.Constant(0)))
		fs.emit(cgarm.branch_cond(target, cgarm.Cond.NE))





def codegen_readln(cs: CodegenState, fs: FuncState, stmt: ir3.ReadLnCall):
	dest = fs.get_location(stmt.name)
	ty = fs.get_type(stmt.name)

	saves, stack_adjust = pre_function_call(cs, fs, stmt.id, dest.register())

	if ty == "String":
		fs.emit(cgarm.call(cs.require_readln_string_function()))
		fs.emit(cgarm.mov(dest.register(), cgarm.A1))

	elif ty == "Bool":
		fs.emit(cgarm.call(cs.require_readln_bool_function()))
		fs.emit(cgarm.mov(dest.register(), cgarm.A1))

	elif ty == "Int":
		fs.emit(cgarm.call(cs.require_readln_int_function()))
		fs.emit(cgarm.mov(dest.register(), cgarm.A1))

	else:
		raise CGException(f"argument to readln has invalid type '{ty}'")

	post_function_call(cs, fs, saves, stack_adjust)



def codegen_println(cs: CodegenState, fs: FuncState, stmt: ir3.PrintLnCall):
	value = get_value(cs, fs, stmt.value)
	ty = get_value_type(cs, fs, stmt.value)

	saves, stack_adjust = pre_function_call(cs, fs, stmt.id)

	# strings are always in registers
	if ty == "String":
		fs.emit(cgarm.mov(cgarm.A2, value))

		# for strings specifically, increment by 4 to skip the length. the value is a pointer anyway.
		fs.emit(cgarm.add(cgarm.A2, cgarm.A2, cgarm.Constant(4)))

		# yes, we can use puts, but for consistency with always putting the argument
		# in 'a2', we use printf.
		fs.emit(cgarm.load_label(cgarm.A1, cs.add_string("%s\n") + "_raw"))
		fs.emit(cgarm.call("printf(PLT)"))

	elif ty == "Int":
		# if value is in a1, we want to move it to a2 before we clobber it
		fs.emit(cgarm.mov(cgarm.A2, value))
		fs.emit(cgarm.load_label(cgarm.A1, cs.add_string("%d\n") + "_raw"))
		fs.emit(cgarm.call("printf(PLT)"))

	elif ty == "Bool":
		# update the condition flags here, so that we can elide an additional 'cmp a1, #0'
		fs.emit(cgarm.mov_s(cgarm.A2, value))

		fs.emit(cgarm.load_label(cgarm.A2, cs.add_string("false") + "_raw").conditional(cgarm.Cond.EQ))
		fs.emit(cgarm.load_label(cgarm.A2, cs.add_string("true") + "_raw").conditional(cgarm.Cond.NE))

		fs.emit(cgarm.load_label(cgarm.A1, cs.add_string("%s\n") + "_raw"))
		fs.emit(cgarm.call("printf(PLT)"))

	elif ty == "$NullObject":
		fs.emit(cgarm.load_label(cgarm.A2, cs.add_string("null") + "_raw"))
		fs.emit(cgarm.load_label(cgarm.A1, cs.add_string("%s\n") + "_raw"))

		fs.emit(cgarm.call("printf(PLT)"))

	else:
		raise CGException(f"argument to println has invalid type '{ty}'")

	post_function_call(cs, fs, saves, stack_adjust)




def pre_function_call(cs: CodegenState, fs: FuncState, stmt_id: int,
	dest_reg: Optional[cgarm.Register] = None) -> Tuple[List[cgarm.Register], int]:
	# for each of a1-a4, if there is some value in there, we need to save/restore across
	# the call boundary. this also acts as a spill for those values, so we don't need to
	# handle spilling separately.
	saves: List[cgarm.Register] = []
	for r in ["a1", "a2", "a3", "a4"]:
		# we check that the register is live at any of our successors.
		# if it's not, then even if it's live on this statement, we don't need to save it
		if any(map(lambda x: fs.is_register_live(r, x), fs.stmt_successors[stmt_id])):
			saves.append(cgarm.Register(r))

	# ... if the destination of the call is one of these clobbered registers,
	# then don't even bother saving it.
	if dest_reg is not None and dest_reg in saves:
		saves.remove(dest_reg)

	# need to align the stack. we always save 'lr', so that's an auto +4 already
	if (4 + fs.current_stack_offset() + 4 * len(saves)) % STACK_ALIGNMENT == 0:
		stack_adjust = 0

	else:
		fs.stack_push_32n(1).annotate("align adjustment (pre)")
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
		fs.stack_pop_32n(stack_adjust).annotate("align adjustment (post)")





def codegen_storestackarg(cs: CodegenState, fs: FuncState, stmt: ir3.StoreFunctionStackArg):
	# calculate the offset it needs to be moved
	offset = stmt.arg_num - 4

	# the offset needs to be fixed up in the actual call once we know how many caller-saved
	# args we need to push.
	val = fs.get_location(stmt.var).register()

	# very hacky. very very hacky.
	stmt.gen_instr = cgarm.store(val, cgarm.Memory(cgarm.SP, -(offset + 1) * 4))
	fs.emit(stmt.gen_instr)



def codegen_call(cs: CodegenState, fs: FuncState, call: ir3.FnCall, dest_reg: cgarm.Register, stmt_id: int):
	# if the number of arguments is > 4, then we set up the stack first; this
	# is so we can just use a1 as a scratch register

	# sorry to disappoint, but we need backpatching now. first, generate the instruction
	# to save whichever of a1-a4 we need to save
	old_ofs = fs.stack_extra_offset
	saves, stack_adjust = pre_function_call(cs, fs, stmt_id, dest_reg = dest_reg)

	# then, for each of the things, add the extra offset.
	for storer in call.stack_stores:
		extra_ofs = fs.stack_extra_offset - old_ofs
		victim = cast(cgarm.Instruction, storer.gen_instr)

		assert victim is not None
		assert victim.instr == "str"
		assert victim.operands[1].is_memory()

		cast(cgarm.Memory, victim.operands[1]).offset -= extra_ofs


	if len(call.args) > 4:

		# allocate the whole block at a time (instead of doing pushes)
		fs.stack_push_32n(len(call.args) - 4)

		# to match the C calling convention, stack arguments go right-to-left.
		for i, arg in enumerate(reversed(call.args[4:])):
			if isinstance(arg, ir3.VarRef) and arg.name in call.ignored_var_uses:
				continue

			# just always use a1 as a hint, since it's bound to get spilled anyway
			# note the stack offset is always -4, since we do the post increment
			val = get_value(cs, fs, arg)
			ofs = i * 4

			if val.is_constant():
				fs.emit(cgarm.mov(cgarm.A1, val))
				fs.emit(cgarm.store(cgarm.A1, cgarm.Memory(cgarm.SP, ofs)))

			else:
				assert val.is_register()
				fs.emit(cgarm.store(val, cgarm.Memory(cgarm.SP, ofs)))


	# this is a little scuffed, but there can be instances where, eg. we need to
	# move a4 -> a3, a3 -> a2, a2 -> a1 (or the reverse). in such situations, the
	# order matters...
	ordering: List[Tuple[int, str, str, cgarm.Operand]] = []

	for i, arg in enumerate(call.args[:4]):
		val = get_value(cs, fs, arg)
		if val.is_register():
			ordering.append((i, f"a{i + 1}", cast(cgarm.Register, val).name, val))
		else:
			ordering.append((i, f"a{i + 1}", "", val))


	while len(ordering) > 0:

		# for each thingy:
		flag = False
		# print(f"ordering = {ordering}")

		for idx, (i, dst, src, val) in enumerate(ordering):
			# see if anybody else sets our src
			if src == dst or len(list(filter(lambda s: s == dst, map(lambda f: f[2], ordering)))) == 0:
				# nobody does; we can generate now
				fs.emit(cgarm.mov(cgarm.Register(f"a{i + 1}"), val))
				ordering.pop(idx)
				flag = True
				break

		if not flag:
			raise CGException("failed to find a proper ordering to set arguments!")

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

	elif isinstance(stmt, ir3.ReadLnCall):
		codegen_readln(cs, fs, stmt)

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

	elif isinstance(stmt, ir3.StoreFunctionStackArg):
		codegen_storestackarg(cs, fs, stmt)

	elif isinstance(stmt, cgpseudo.DummyStmt):
		pass

	else:
		raise CGException(f"statement '{type(stmt)}' not implemented")





def codegen_method(cs: CodegenState, method: ir3.FuncDefn):
	assigns, spills, reg_live_ranges, defined_on_entry = cgreg.allocate_registers(method)

	if options.should_print_lowered_ir():
		print(f"{method}")

	# setup the function state
	fs = FuncState(cs, method, assigns, spills, reg_live_ranges, defined_on_entry)

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


	if (fn := cs.get_string_concat_function()) in cs.needed_builtins:
		cs.emit_raw(f"""
.global {fn}
.type {fn}, %function
{fn}:
	@ takes two args: (the strings, duh) and returns 1 (the result, duh)
	@ anything + null = anything; null + null = null.
	stmfd sp!, {{v1, v2, v3, v4, v5, fp, lr}}
	mov v1, a1              @ save the string pointers into not-a1 and not-a2
	mov v2, a2
	cmp v1, #0              @ check left for null
	moveq a1, v2            @ if null return right
	beq .{fn}_exit
	cmp v2, #0              @ check right for null
	moveq a1, v1            @ if null return left
	beq .{fn}_exit
	ldr v4, [v1, #0]        @ load the lengths of the two strings
	ldr v5, [v2, #0]
	add v3, v4, v5          @ get the new length; a1 contains the +5 (for length + null term)
	add a2, v3, #5          @ v3 = the real length
	mov a1, #1
	bl calloc(PLT)          @ malloc some memory (memory in a1)
	mov fp, a1              @ save the return pointer
	str v3, [a1, #0]        @ store the length (v3)
	add a1, a1, #4          @ dst
	add a2, v1, #4          @ src - string 1
	mov a3, v4              @ len - string 1
	bl memcpy(PLT)          @ memcpy returns dst.
	add a1, fp, v4
	add a1, a1, #4
	add a2, v2, #4          @ src - string 2
	mov a3, v5              @ len - string 2
	bl memcpy(PLT)          @ copy the second string
	mov a1, fp              @ return value
.{fn}_exit:
	ldmfd sp!, {{v1, v2, v3, v4, v5, fp, pc}}
""")

	if (fn := cs.get_string_compare_function()) in cs.needed_builtins:
		cs.emit_raw(f"""
.global {fn}
.type {fn}, %function
{fn}:
	@ takes two args: (the strings, duh) and returns 1 if they are equal, and 0 otherwise.
	stmfd sp!, {{lr}}
	cmp a1, a2              @ if the pointers are equal, then they are trivially equal
	moveq a1, #1            @ return 0
	beq .{fn}_exit          @ and exit
	cmp a1, #0              @ check left and right for null
	moveq a1, #0            @ if the pointers not equal but one of them is null,
	beq .{fn}_exit          @ then they will never be equal
	cmp a2, #0              @ right side
	moveq a2, #0
	beq .{fn}_exit
	add a1, a1, #4          @ offset by 4 to skip the length
	add a2, a2, #4
	bl strcmp(PLT)
	cmp a1, #0              @ strcmp returns 0 for equal, nonzero otherwise
	moveq a1, #1
	movne a1, #0
.{fn}_exit:
	ldmfd sp!, {{pc}}
""")



	if (fn := cs.get_divide_function()) in cs.needed_builtins:
		cs.emit_raw(f"""
.global {fn}
.type {fn}, %function
{fn}:
	@ takes two args: (dividend, divisor) and returns the quotient.
	stmfd sp!, {{v1, v2, v3, v4, v5, fp, lr}}
	cmp a2, #0              @ check if we're dividing by 0. if so, just quit.
	beq .{fn}_exit
	movs v4, a1, asr #31    @ sign bit (1 if negative)
	rsbne a1, a1, #0        @ negate if the sign bit was set (ie. abs)
	movs v5, a2, asr #31    @ also sign bit
	rsbne a2, a2, #0        @ negate if the sign bit was set (ie. abs)
	mov v3, #0              @ store the quotient
.{fn}_L1:
	subs a1, a1, a2         @ check if we're done
	blt .{fn}_done
	add v3, v3, #1
	b .{fn}_L1
.{fn}_done:
	mov a1, v3
	eors v1, v4, v5         @ check if the sign bits are different
	rsbne a1, a1, #0        @ negate if so
.{fn}_exit:
	ldmfd sp!, {{v1, v2, v3, v4, v5, fp, pc}}
""")

	if (fn := cs.get_readln_int_function()) in cs.needed_builtins:
		scanf_int = cs.add_string(" %d ")
		cs.emit_raw(f"""
.global {fn}
.type {fn}, %function
{fn}:
	@ takes no args and returns the int
	stmfd sp!, {{lr}}
	sub sp, sp, #4          @ save some stack space (scanf wants a pointer)
	mov a2, sp              @ a2 is the pointer argument
	ldr a1, ={scanf_int}_raw
	bl scanf(PLT)
	cmp a1, #1              @ if scanf returned < 1...
	bge .{fn}_ok
	mov a1, #0              @ just return 0.
	b .{fn}_exit
.{fn}_ok:
	ldr a1, [sp, #0]        @ load the value from stack
.{fn}_exit:
	add sp, sp, #4          @ restore the stack
	ldmfd sp!, {{pc}}
""")

	if (fn := cs.get_readln_bool_function()) in cs.needed_builtins:
		scanf_bool = cs.add_string(" %7s ")
		cs.emit_raw(f"""
.global {fn}
.type {fn}, %function
{fn}:
	@ takes no args and returns the bool
	@ accepts: '1_' (anything starting with '1', or 'T_'/'t_' (anything starting with 't')
	@ anything else is false.
	stmfd sp!, {{lr}}
	sub sp, sp, #12          @ space for the buffer
	mov a2, sp
	ldr a1, ={scanf_bool}_raw
	bl scanf(PLT)
	cmp a1, #1              @ if scanf returned < 1, then it's probably eof?
	blt .{fn}_false
	ldrb a1, [sp, #0]       @ otherwise, load the first char
	cmp a1, #49             @ 49 = '1'
	beq .{fn}_true
	cmp a1, #84             @ 84 = 'T'
	beq .{fn}_true
	cmp a1, #116            @ 116 = 't'
	beq .{fn}_true
.{fn}_false:
	mov a1, #0
	b .{fn}_exit
.{fn}_true:
	mov a1, #1
.{fn}_exit:
	add sp, sp, #12
	ldmfd sp!, {{pc}}
""")

	if (fn := cs.get_readln_string_function()) in cs.needed_builtins:
		cs.emit_raw(f"""
.global {fn}
.type {fn}, %function
{fn}:
	@ takes no args and returns the string
	stmfd sp!, {{v1, lr}}
	mov a1, #256            @ allocate 256 for the actual string
	add a1, a1, #5          @ plus 4 (len) + 1 (null term)
	mov a2, #1
	bl calloc(PLT)
	mov v1, a1              @ save it
	add a1, a1, #4          @ skip the length (will write later)
	mov a2, #256            @ buffer len
	ldr a3, =stdin
	ldr a3, [a3, #0]
	bl fgets(PLT)           @ 'a1' is now the string
	cmp a1, #0
	beq .{fn}_bar
	bl strlen(PLT)          @ get the length
	cmp a1, #0
	beq .{fn}_exit          @ don't do funny stuff (underflow)
	add a3, v1, a1
	add a3, a3, #4
	ldrb a2, [a3, #-1]      @ check the last char...
	cmp a2, #10
	beq .{fn}_trim
	b .{fn}_exit
.{fn}_bar:
	mov a1, #0
	b .{fn}_exit
.{fn}_trim:                 @ get rid of the trailing newline
	mov a4, #0
	strb a4, [a3, #-1]
	sub a1, a1, #1
.{fn}_exit:
	str a1, [v1, #0]        @ write the length
	mov a1, v1              @ return
	ldmfd sp!, {{v1, pc}}
""")


	cs.emit_raw(".data")
	cs.emit_raw(".global stdin")

	for string, id in cs.strings.items():
		cs.emit_raw(f".align 4")
		cs.emit_raw(f".string{id}:")
		cs.emit_raw(f"    .word {len(string)}")
		cs.emit_raw(f".string{id}_raw:")
		cs.emit_raw(f'    .asciz "{escape_string(string)}"')
		cs.comment()

	return cs.lines

