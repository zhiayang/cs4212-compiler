#/usr/bin/env python

from __future__ import annotations
from typing import *
from copy import *

from . import ast
from . import ir3
from . import simp
from . import cglower

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

	log_opt(func, "unreachable block", len(removed_blocks))
	return len(removed_blocks) > 0


def remove_double_jumps(func: ir3.FuncDefn) -> bool:
	# while we're here, prune any blocks that contain just a single unconditional branch.
	# eg. if we have a: { ... jmp b; }, b: { jmp c; }, c: { ... }, then we can replace it
	# with simply a: { ... jmp c; }, c: { ... } and yeet b from existence.

	num_removed = 0
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

			num_removed += 1

	# note that we only eliminate the double jump. the unreachable-block pruning actually
	# removes the "middle" block, since it is now unreachable.

	log_opt(func, "double-jump", num_removed)
	return num_removed > 0


def remove_redundant_temporaries(func: ir3.FuncDefn) -> bool:
	# we often generate slightly scuffed IR like this:
	# _t1 = a + b;
	# m = _t1;
	# this optimisation pass simply checks if a variable (_t1 in this case)
	# is only used once, and that only use is on the next line (in the same block) to assign to someone else.
	# if so, it eliminates the redundant _t1, and does `m = a + b` directly.

	# first, figure out which block each statement is in
	parent_blocks: Dict[int, str] = dict()
	block_names: Dict[str, ir3.BasicBlock] = dict()
	for blk in func.blocks:
		block_names[blk.name] = blk
		for s in blk.stmts:
			parent_blocks[s.id] = blk.name

	num_removed = 0
	for temp in filter(lambda x: x.name.startswith("_"), func.vars):
		assigns = get_var_assigns(func, temp.name)
		# can only be assigned once. anyway for temporary variables we essentially generate SSA,
		# so we shouldn't encounter this case... by right.
		if len(assigns) > 1:
			continue

		ass = assigns[0]
		if not isinstance(ass, ir3.AssignOp):
			continue

		next_id = ass.id + 1

		# not in the same block; i don't want to do flow analysis, so just ignore this.
		if (next_id not in parent_blocks) or (parent_blocks[next_id] != parent_blocks[ass.id]):
			continue

		# get the block...
		block = block_names[parent_blocks[ass.id]]
		next_stmt = next(filter(lambda s: s.id == next_id, block.stmts))

		if isinstance(next_stmt, ir3.AssignOp) or isinstance(next_stmt, ir3.AssignDotOp):
			if isinstance(next_stmt.rhs, ir3.ValueExpr) and isinstance(next_stmt.rhs.value, ir3.VarRef):
				if next_stmt.rhs.value.name == temp.name:
					# ok, we are clear to eliminate this guy. another pass will
					# remove unused variables, so we don't need to check it here
					# (and anyway removing statements will mess up the numbering)
					assert isinstance(ass, ir3.AssignOp)
					next_stmt.rhs = ass.rhs
					num_removed += 1

	log_opt(func, "redundant assignment", num_removed)
	return num_removed > 0


def remove_unused_variables(func: ir3.FuncDefn) -> bool:
	# this is not limited to removing temporary variables. of course,
	# we can't eliminate dotop assigns, but that's fine; otherwise, we
	# can eliminate params, user-defined locals, and temporaries.

	parent_blocks: Dict[int, ir3.BasicBlock] = dict()
	for blk in func.blocks:
		for s in blk.stmts:
			parent_blocks[s.id] = blk

	num_removed = 0
	for var in func.vars[:]:
		uses = get_var_uses(func, var.name)
		if len(uses) == 0:
			assigns = get_var_assigns(func, var.name)
			for ass in assigns:
				parent_blocks[ass.id].stmts.remove(ass)

			func.vars.remove(var)
			num_removed += 1

	log_opt(func, "unused variable", num_removed)
	return num_removed > 0





def optimise(func: ir3.FuncDefn):

	changed = True
	while changed:
		changed = False
		renumber_statements(func)

		changed |= prune_unreachable_blocks(func)
		changed |= remove_double_jumps(func)
		changed |= remove_redundant_temporaries(func)
		changed |= remove_unused_variables(func)






# helpers

def renumber_statements(func: ir3.FuncDefn):
	cglower.renumber_stmts(func)

def log_opt(func: ir3.FuncDefn, kind: str, num: int):
	if num > 0:
		util.log(f"opt: ({func.name}): removed {num} {kind}{'' if num == 1 else 's'}")

def get_var_uses(func: ir3.FuncDefn, var: str) -> List[ir3.Stmt]:
	ret: List[ir3.Stmt] = []
	for blk in func.blocks:
		ret.extend(filter(lambda x: is_var_used_in_stmt(x, var), blk.stmts))

	return ret


def get_var_assigns(func: ir3.FuncDefn, var: str) -> List[ir3.Stmt]:
	ret: List[ir3.Stmt] = []
	for blk in func.blocks:
		ret.extend(filter(lambda x: isinstance(x, ir3.AssignOp) and x.lhs == var, blk.stmts))

	return ret


def is_var_used_in_value(value: ir3.Value, var: str) -> bool:
	return isinstance(value, ir3.VarRef) and value.name == var

def is_var_used_in_expr(expr: ir3.Expr, var: str) -> bool:
	if isinstance(expr, ir3.BinaryOp):
		return is_var_used_in_value(expr.lhs, var) or is_var_used_in_value(expr.rhs, var)

	elif isinstance(expr, ir3.UnaryOp):
		return is_var_used_in_value(expr.expr, var)

	elif isinstance(expr, ir3.DotOp):
		return expr.lhs == var

	elif isinstance(expr, ir3.ValueExpr):
		return is_var_used_in_value(expr.value, var)

	elif isinstance(expr, ir3.FnCallExpr):
		return len(list(filter(None, map(lambda v: is_var_used_in_value(v, var), expr.call.args)))) > 0

	else:
		return False

def is_var_used_in_stmt(stmt: ir3.Stmt, var: str) -> bool:
	if isinstance(stmt, ir3.FnCallStmt):
		return len(list(filter(None, map(lambda v: is_var_used_in_value(v, var), stmt.call.args)))) > 0

	elif isinstance(stmt, ir3.AssignOp) or isinstance(stmt, ir3.AssignDotOp):
		return is_var_used_in_expr(stmt.rhs, var)

	elif isinstance(stmt, ir3.ReturnStmt):
		return is_var_used_in_value(stmt.value, var) if stmt.value is not None else False

	elif isinstance(stmt, ir3.ReadLnCall):
		return stmt.name == var

	elif isinstance(stmt, ir3.PrintLnCall):
		return is_var_used_in_value(stmt.value, var)

	elif isinstance(stmt, ir3.CondBranch):
		if isinstance(stmt.cond, ir3.RelOp):
			return is_var_used_in_value(stmt.cond.lhs, var) or is_var_used_in_value(stmt.cond.rhs, var)
		else:
			return is_var_used_in_value(stmt.cond, var)

	else:
		return False
