#!/usr/bin/env python

from __future__ import annotations
from abc import ABC, abstractmethod
from typing import *
from copy import *

from .util import Location, CGException, print_warning, escape_string


class Operand(ABC):
	@abstractmethod
	def __str__(self) -> str: ...

	@classmethod
	def kind_str(cls) -> str:
		if cls == Register:
			return "a register"
		elif cls == Constant:
			return "a constant"
		elif cls == Memory:
			return "memory"
		else:
			return "???"



class Register(Operand):
	reg_numbers = {
		"a1":  0, "a2":  1, "a3":  2, "a4":  3,
		"v1":  4, "v2":  5, "v3":  6, "v4":  7,
		"v5":  8, "v6":  9, "v7": 10, "fp": 11,
		"ip": 12, "sp": 13, "lr": 14, "pc": 15
	}

	def __init__(self, name: str) -> None:
		self.name = name
		self.number = Register.reg_numbers[name]
		self.exclaim = False

	def post_incr(self) -> Register:
		ret = Register(self.name)
		ret.exclaim = True
		return ret

	def __eq__(self, other: object) -> bool:
		if not isinstance(other, Register):
			return False

		return (self.name == other.name) and (self.number == other.number)

	def __str__(self) -> str:
		if self.exclaim:
			return f"{self.name}!"
		else:
			return self.name


class Memory(Operand):
	def __str__(self) -> str:
		return f"uwu"



class Constant(Operand):
	def __init__(self, value: int, is_memory: bool = False) -> None:
		self.value = value
		self.is_memory = is_memory

	def is_small(self) -> bool:
		return (-256 <= self.value <= 256)

	def as_memory(self) -> Constant:
		return Constant(self.value, is_memory = True)

	def __str__(self) -> str:
		if self.is_memory:
			return f"=#{self.value}"
		else:
			return f"#{self.value}"




class Instruction():
	def __init__(self, mnemonic: str, operands: List[Operand], raw_ops: str = "", is_label: bool = False):
		self.instr = mnemonic
		self.operands = operands
		self.raw_operand = raw_ops
		self.annotations: List[str] = []
		self.is_label = is_label

	def annotate(self, msg: str) -> Instruction:
		self.annotations.append(msg)
		return self

	def __str__(self) -> str:
		if self.is_label:
			return f"{self.instr}:"

		foo = f"{self.instr} {', '.join(map(str, self.operands))}"
		if self.raw_operand != "":
			if len(self.operands) > 0:
				foo += f", {self.raw_operand}"
			else:
				foo += self.raw_operand

		if len(self.annotations) > 0:
			a_spaces = ' ' * max(0, 40 - len(foo))
			annots = f"{a_spaces}@ {'; '.join(self.annotations)}"
		else:
			annots = ""

		return f"{foo}{annots}"


	@staticmethod
	def raw(instr: str) -> Instruction:
		return Instruction(instr, [])








def ensure_operand_kind(instr: str, op: Operand, nth: str, kind: Type[Operand]):
	if not isinstance(op, kind):
		raise CGException(f"{nth} operand for '{instr}' must be {kind.kind_str()}")



def add(dest: Operand, op1: Operand, op2: Operand) -> Instruction:
	ensure_operand_kind("add", dest, "destination", Register)

	# emit a constant move after adding the values.
	if isinstance(op1, Constant) and isinstance(op2, Constant):
		return mov(dest, Constant(op1.value + op2.value))

	return Instruction("add", [ dest, op1, op2 ])



def sub(dest: Operand, op1: Operand, op2: Operand) -> Instruction:
	ensure_operand_kind("sub", dest, "destination", Register)

	# emit a constant move
	if isinstance(op1, Constant) and isinstance(op2, Constant):
		return mov(dest, Constant(op1.value - op2.value))

	# if the first operand is a constant, switch this to an rsb and swap.
	if isinstance(op1, Constant):
		return rsb(dest, op2, op1)

	return Instruction("sub", [ dest, op1, op2 ])



def rsb(dest: Operand, op1: Operand, op2: Operand) -> Instruction:
	ensure_operand_kind("rsb", dest, "destination", Register)

	# emit a constant move
	if isinstance(op1, Constant) and isinstance(op2, Constant):
		return mov(dest, Constant(op2.value - op1.value))

	# if the first operand is a constant, switch this to a sub and swap.
	if isinstance(op1, Constant):
		return sub(dest, op2, op1)

	return Instruction("rsb", [ dest, op1, op2 ])


def mul(dest: Operand, op1: Operand, op2: Operand):
	pass



def branch(label: str) -> Instruction:
	return Instruction("b", [], label)


def label(label: str) -> Instruction:
	return Instruction(label, [], is_label = True)


def mov(dest: Operand, src: Operand) -> Instruction:
	ensure_operand_kind("mov", dest, "destination", Register)

	if isinstance(src, Register):
		return Instruction("mov", [ dest, src ])

	elif isinstance(src, Constant):
		if src.is_small():
			return Instruction("mov", [ dest, src ])
		else:
			return Instruction("ldr", [ dest, src.as_memory() ])

	else:
		raise CGException("source operand for 'mov' must be either a register or a constant")



def load(dest: Operand, src: Operand) -> Instruction:
	ensure_operand_kind("ldr", dest, "destination", Register)
	ensure_operand_kind("ldr", src, "source", Memory)
	return Instruction("ldr", [ dest, src ])


def store(src: Operand, dest: Operand) -> Instruction:
	ensure_operand_kind("str", src, "source", Register)
	ensure_operand_kind("str", dest, "destination", Memory)
	return Instruction("str", [ src, dest ])


def store_multiple(ptr: Register, regs: Iterable[Register]) -> Instruction:
	sorted_regs = sorted(regs, key = lambda r: Register.reg_numbers[r.name])
	return Instruction("stmfd", [ ptr.post_incr() ], f"{{{', '.join(map(str, sorted_regs))}}}")

def load_multiple(ptr: Register, regs: Iterable[Register]) -> Instruction:
	sorted_regs = sorted(regs, key = lambda r: Register.reg_numbers[r.name])
	return Instruction("ldmfd", [ ptr.post_incr() ], f"{{{', '.join(map(str, sorted_regs))}}}")



# globals... kekw
A1 = Register("a1")
A2 = Register("a2")
A3 = Register("a3")
A4 = Register("a4")
V1 = Register("v1")
V2 = Register("v2")
V3 = Register("v3")
V4 = Register("v4")
V5 = Register("v5")
V6 = Register("v6")
V7 = Register("v7")
FP = Register("fp")
IP = Register("ip")
SP = Register("sp")
LR = Register("lr")
PC = Register("pc")

