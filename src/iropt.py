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
		for stmt in block.stmts:
			if isinstance(stmt, ir3.Branch):
				ret = ret.union(check_reachability(block_names[stmt.label], seen.union(ret)))

			elif isinstance(stmt, ir3.CondBranch):
				ret = ret.union(check_reachability(block_names[stmt.label], seen.union(ret)))

		return ret


	# keep removing things until nothing changes.
	visited: Set[str] = set()

	removed_blocks = []
	while True:
		new_visited = check_reachability(func.blocks[0], set())
		if new_visited == visited:
			break

		visited = new_visited

		# remove any blocks that are not reachable
		unreachables = set(func.blocks).difference(map(lambda x: block_names[x], visited))
		for unr in unreachables:
			func.blocks.remove(unr)
			removed_blocks.append(unr)
			print(f"removing {unr.name}")

	for rem in removed_blocks:
		for blk in func.blocks:
			blk.predecessors.discard(rem)

	if len(removed_blocks) > 0:
		util.log(f"opt: ({func.name}): removed {len(removed_blocks)} unreachable blocks")

	return len(removed_blocks) > 0




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

	if len(removed_blocks) > 0:
		util.log(f"opt: ({func.name}): eliminated {len(removed_blocks)} double-jumps")

	return len(removed_blocks) > 0






def optimise(func: ir3.FuncDefn):

	changed = True
	while changed:
		changed = False

		changed = changed or prune_unreachable_blocks(func)
		changed = changed or remove_double_jumps(func)
