#!/usr/bin/env python

from __future__ import annotations
from typing import *
from copy import *

from . import cgarm

from .cgstate import *


def optimise(fs: FuncState):
	# return

	passes = 0
	while True:
		passes += 1

		if remove_redundant_branches(fs):
			continue

		if remove_redundant_consecutive_loads_stores(fs):
			continue

		if remove_redundant_load_store(fs):
			continue

		if optimise_conditional_branches(fs):
			continue

		if remove_redundant_arithmetic(fs):
			continue

		break



def remove_redundant_branches(fs: FuncState) -> bool:
	for i, instr in enumerate(fs.instructions):
		if i + 1 == len(fs.instructions):
			break

		if (instr.instr == "b") and fs.instructions[i + 1].is_label:
			if instr.raw_operand == fs.instructions[i + 1].instr:
				# pop the branch. we can't yeet the label cos someone else may jump to it.
				fs.instructions.pop(i)
				return True

	return False


def remove_redundant_consecutive_loads_stores(fs: FuncState) -> bool:
	# note: labels appear in the instruction stream, so they will interrupt this
	# optimisation if the loads/stores are not in the same basic block.
	for i, instr in enumerate(fs.instructions):
		if i + 1 == len(fs.instructions):
			break

		in1 = instr
		in2 = fs.instructions[i + 1]

		if (in1.instr == "str" or in1.instr == "ldr") and in1 == in2:

			# can't do this; they have side effects.
			if cast(cgarm.Memory, in1.operands[1]).post_incr or cast(cgarm.Memory, in2.operands[1]).post_incr:
				continue

			# remove one of them.
			fs.instructions.pop(i)
			return True

	return False


def remove_redundant_load_store(fs: FuncState) -> bool:
	# ldr <A>, <MEM>
	# str <A>, <MEM>
	# where the A and MEM are the same (and they are in the same BB);
	# the store is redundant.
	# (BB-sameness is enforced as explained above)
	for i, instr in enumerate(fs.instructions):
		if i + 1 == len(fs.instructions):
			break

		in1 = instr
		in2 = fs.instructions[i + 1]

		if (in1.instr == "ldr" and in2.instr == "str"):
			if in1.is_label or in2.is_label:    # ????
				continue

			# good thing is that they are in the same order.
			if (in1.raw_operand != in2.raw_operand) or (in1.operands != in2.operands):
				continue

			# can't do this; they have side effects.
			if cast(cgarm.Memory, in1.operands[1]).post_incr or cast(cgarm.Memory, in2.operands[1]).post_incr:
				continue

			# ok, we can remove the store.
			fs.instructions.pop(i + 1)
			return True


		# use the annotations!
		if "caller-restore" in in1.annotations and "caller-save" in in2.annotations:
			if in1.instr != "ldmfd" or in2.instr != "stmfd":
				continue

			if (in1.operands != in2.operands) or (in1.raw_operand != in2.raw_operand):
				continue

			# both must have side effects
			if not cast(cgarm.Register, in1.operands[0]).exclaim or not cast(cgarm.Register, in2.operands[0]).exclaim:
				continue

			# now, the store can be eliminated.
			fs.instructions.pop(i + 1)

			# BUT, we get rid of the post-incr from the load so the stack position doesn't change.
			cast(cgarm.Register, in1.operands[0]).exclaim = False
			return True

	return False


def remove_redundant_arithmetic(fs: FuncState) -> bool:
	num_removed = 0
	for instr in fs.instructions[:]:
		# mov a, a
		if instr.instr == "mov":
			if len(instr.operands) != 2:
				continue

			if instr.operands[0] == instr.operands[1]:
				fs.instructions.remove(instr)
				num_removed += 1

		# add a, a, 0
		# sub a, a, 0
		if instr.instr == "add" or instr.instr == "sub":
			if len(instr.operands) != 3:
				continue

			if instr.operands[0] == instr.operands[1] and instr.operands[2].is_constant():
				if cast(cgarm.Constant, instr.operands[2]).value == 0:
					fs.instructions.remove(instr)
					num_removed += 1

	return num_removed > 0


def optimise_conditional_branches(fs: FuncState) -> bool:
	# given something like this:
	# cmp v2, v1                              @ _t3 = k == _c20;
	# moveq v1, #1
	# movne v1, #0
	# cmp v1, #0                              @ if (_t3) goto .L1;
	# bne ._J3Foo_3fooiiiiiE_L1

	# we want to turn it into 2 instructions:
	# cmp v2, v1
	# beq ._J3Foo_3fooiiiiiE_L1

	conditions = set([ "eq", "ne", "lt", "gt", "le", "ge" ])

	for i in range(0, len(fs.instructions)):
		window = fs.instructions[i:i+5]
		if len(window) < 5:
			break

		if window[0].instr != "cmp":
			continue

		# same check for both of them -- must be a valid conditional move
		if window[1].instr[:3] != "mov" or window[1].instr[3:] not in conditions:
			continue
		if window[2].instr[:3] != "mov" or window[2].instr[3:] not in conditions:
			continue

		# match the second operand
		if window[1].operands[0] != window[2].operands[0]:
			continue

		cmov_reg = window[1].operands[0]

		# we want to use the condition for the first one as our branch condition.
		# that is the order we use, don't change it.
		cmov_cond = window[1].instr[3:]

		if (window[1].operands[1] != cgarm.Constant(1)) or (window[2].operands[1] != cgarm.Constant(0)):
			continue

		if window[3].instr != "cmp" or window[3].operands != [ cmov_reg, cgarm.Constant(0) ]:
			continue

		# lastly, check that the thing is a conditional branch
		if (window[4].instr[0] == 'b') and (window[4].instr[1:] in conditions):
			# we are ok to optimise.
			new_instr = cgarm.branch_cond(window[4].raw_operand, cgarm.Condition(cmov_cond))

			# now replace the second instruction
			fs.instructions[i + 1] = new_instr

			# and yeet 3
			fs.instructions.pop(i + 2)
			fs.instructions.pop(i + 2)  # not a typo
			fs.instructions.pop(i + 2)  # not a typo
			return True


	return False

