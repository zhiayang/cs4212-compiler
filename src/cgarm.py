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

	def __eq__(self, other: object) -> bool:
		if not isinstance(other, Register):
			return False

		return (self.name == other.name) and (self.number == other.number)

	def __str__(self) -> str:
		return self.name

	@staticmethod
	def A1() -> Register:
		return Register("a1")

	@staticmethod
	def A2() -> Register:
		return Register("a2")

	@staticmethod
	def A3() -> Register:
		return Register("a3")

	@staticmethod
	def A4() -> Register:
		return Register("a4")

	@staticmethod
	def V1() -> Register:
		return Register("v1")

	@staticmethod
	def V2() -> Register:
		return Register("v2")

	@staticmethod
	def V3() -> Register:
		return Register("v3")

	@staticmethod
	def V4() -> Register:
		return Register("v4")

	@staticmethod
	def V5() -> Register:
		return Register("v5")

	@staticmethod
	def V6() -> Register:
		return Register("v6")

	@staticmethod
	def V7() -> Register:
		return Register("v7")

	@staticmethod
	def FP() -> Register:
		return Register("fp")

	@staticmethod
	def IP() -> Register:
		return Register("ip")

	@staticmethod
	def SP() -> Register:
		return Register("sp")

	@staticmethod
	def LR() -> Register:
		return Register("lr")

	@staticmethod
	def PC() -> Register:
		return Register("pc")



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
	def __init__(self, mnemonic: str, operands: List[Operand], raw_ops: str = ""):
		self.instr = mnemonic
		self.operands = operands
		self.raw_operand = raw_ops
		self.annotations: List[str] = []

	def annotate(self, msg: str) -> Instruction:
		self.annotations.append(msg)
		return self

	def __str__(self) -> str:
		foo = f"{self.instr} {', '.join(map(str, self.operands))}"
		if self.raw_operand != "":
			if len(self.operands) > 0:
				foo += f", {self.raw_operand}"
			else:
				foo += self.raw_operand

		a_spaces = ' ' * max(0, 40 - len(foo))
		return f"{foo}{a_spaces}@ {'; '.join(self.annotations)}"


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
