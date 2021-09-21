# StringView.py

# necessary, if not we can't annotate -> Self because this language is bad.
from __future__ import annotations
from typing import *

class StringView:
	@overload
	def __init__(self, data: str) -> None: ...

	@overload
	def __init__(self, data: bytes) -> None: ...

	def __init__(self, data: Union[str, bytes, memoryview]) -> None:
		self.buffer: memoryview

		if isinstance(data, str):
			self.buffer = memoryview(data.encode(encoding = "utf-8"))
		elif isinstance(data, bytes):
			self.buffer = memoryview(data)
		elif isinstance(data, memoryview):
			self.buffer = data
		else:
			raise TypeError(f"invalid type {type(data)}")

	def size(self) -> int:
		return len(self.buffer)

	def string(self) -> str:
		return str(self.buffer, "utf-8")

	def drop(self, n: int) -> StringView:
		return StringView(self.buffer[n:])

	def drop_last(self, n: int) -> StringView:
		return StringView(self.buffer[:max(0, self.size() - n)])

	def take(self, n: int) -> StringView:
		return StringView(self.buffer[:n])

	def take_prefix(self, n: int) -> StringView:
		ret: StringView = self.take(n)
		self.buffer = self.buffer[n:]
		return ret

	def take_while(self, fn: Callable[[str], bool]) -> StringView:
		to_take: int = 0
		while fn(chr(self.buffer[to_take])):
			to_take += 1

		return self.take(to_take)

	def remove_prefix(self, n: int) -> StringView:
		self.buffer = self.buffer[n:]
		return self

	@overload
	def starts_with(self, s: str) -> bool: ...

	@overload
	def starts_with(self, s: bytes) -> bool: ...

	def starts_with(self, s: Union[str, bytes]) -> bool:
		if self.size() < len(s):
			return False
		if isinstance(s, str):
			return str(self.buffer[:len(s)], "utf-8") == s
		elif isinstance(s, bytes):
			return memoryview(s)[:len(s)] == memoryview(s)
		else:
			raise TypeError(f"invalid type {type(s)}")

	def starts_with_one_of(self, s: Union[str, bytes]) -> bool:
		if self.empty():
			return False

		# for c in s:
		# 	if self.buffer[0] == (ord(c) if isinstance(s, str) else c):
		# 		return True
		if isinstance(s, str):
			for c in s:
				if self.buffer[0] == ord(c):
					return True
		elif isinstance(s, bytes):
			for x in s:
				if self.buffer[0] == x:
					return True
		else:
			raise TypeError(f"invalid type {type(s)}")

		return False

	def clone(self) -> StringView:
		return StringView(self.buffer)

	def empty(self) -> bool:
		return self.size() == 0

	def __len__(self) -> int:
		return self.size()

	def __str__(self) -> str:
		return self.string()

	@overload
	def __getitem__(self, index: int) -> int: ...

	@overload
	def __getitem__(self, index: slice) -> StringView: ...

	def __getitem__(self, index: Union[int, slice]) -> Union[int, StringView]:
		if isinstance(index, int):
			return self.buffer[index]
		elif isinstance(index, slice):
			return StringView(self.buffer[index])
		else:
			raise TypeError(f"invalid type {type(index)}")


