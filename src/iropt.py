#/usr/bin/env python

from __future__ import annotations
from typing import *
from copy import *

from . import ast
from . import ir3
from . import simp

from . import util


def prune_unreachable_blocks(func: ir3.FuncDefn) -> bool:
	block_names: Dict[str, ir3.BasicBlock] = {}
	for block in func.blocks:
		block_names[block.name] = block

	def check_reachability(block: ir3.BasicBlock, seen: Set[str]) -> Set[str]:
		ret: Set[str] = set()
		ret.add(block.name)
		if block.name in seen:
			return ret

		# again, we need some workarounds because ir3's branch is *not* a basic-block style jump
		if len(block.stmts) == 0:
			return ret

		elif isinstance(block.stmts[-1], ir3.Branch):
			ret = ret.union(check_reachability(block_names[cast(ir3.Branch, block.stmts[-1]).label], seen.union(ret)))

		elif isinstance(block.stmts[-1], ir3.CondBranch):
			# get the subsequent block via a very inefficient method.
			next_blk: Optional[ir3.BasicBlock] = None

			for i in range(0, len(func.blocks)):
				if func.blocks[i].name == block.name:
					if i + 1 < len(func.blocks):
						next_blk = func.blocks[i + 1]
						break

			br = cast(ir3.CondBranch, block.stmts[-1])
			ret = ret.union(check_reachability(block_names[br.label], seen.union(ret)))

			if next_blk is not None:
				ret = ret.union(check_reachability(next_blk, seen.union(ret)))

		return ret


	# keep removing things until nothing changes.
	visited: Set[str] = set()

	num_removed = 0
	while True:
		new_visited = check_reachability(func.blocks[0], set())
		if new_visited == visited:
			break

		visited = new_visited

		# remove any blocks that are not reachable
		unreachables = set(func.blocks).difference(map(lambda x: block_names[x], visited))
		num_removed += len(unreachables)
		for unr in unreachables:
			func.blocks.remove(unr)

	util.log(f"opt: ({func.name}): removed {num_removed} unreachable blocks")
	return num_removed > 0




def remove_double_jumps(func: ir3.FuncDefn) -> bool:
	# while we're here, prune any blocks that contain just a single unconditional branch.
	# eg. if we have a: { ... jmp b; }, b: { jmp c; }, c: { ... }, then we can replace it
	# with simply a: { ... jmp c; }, c: { ... } and yeet b from existence.

	removed_blocks = []
	# do this weird slice thing to make a copy so we can yeet elements while iterating.
	for blk in func.blocks[:]:
		if len(blk.stmts) == 1 and isinstance(blk.stmts[0], ir3.Branch):
			target = blk.stmts[0].label

			# replace all predecessors to jump to the new target. note (again) that, because
			# ir3 doesn't have proper `if {cond} goto {label} else goto {label}` forms, we need
			# to actually check the last *TWO* statements in a block.

			for pred in blk.predecessors:
				last2 = blk.stmts[-2:]
				for j in last2:
					if isinstance(j, ir3.Branch) and j.label == blk.name:
						j.label = target
					elif isinstance(j, ir3.CondBranch) and j.label == blk.name:
						j.label = target

			removed_blocks.append(blk)
			func.blocks.remove(blk)

	for rem in removed_blocks:
		for blk in func.blocks:
			blk.predecessors.discard(rem)

	util.log(f"opt: ({func.name}): eliminated {len(removed_blocks)} double-jumps")
	return len(removed_blocks) > 0






def optimise(func: ir3.FuncDefn):

	changed = True
	while changed:
		changed = False

		# changed = changed or prune_unreachable_blocks(func)
		# changed = changed or remove_double_jumps(func)
