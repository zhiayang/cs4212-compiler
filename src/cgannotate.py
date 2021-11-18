#!/usr/bin/env python

from __future__ import annotations
from typing import *
from copy import *


__annotations_enabled = True

def annotating() -> bool:
	global __annotations_enabled
	return __annotations_enabled

def enable_annotations(en: bool = True):
	global __annotations_enabled
	__annotations_enabled = en

def disable_annotations():
	global __annotations_enabled
	__annotations_enabled = False





def annotate_reg_allocs(assigns: Dict[str, str], spills: Set[str]) -> Tuple[List[str], List[str]]:
	assign_lines: List[str] = ["assigns: "]

	max_var_len = 7 + max(map(lambda x: len(x), assigns))

	assign_list: Iterable = list(map(lambda x: (x, assigns[x]), assigns))
	assign_list = sorted(assign_list, key = lambda x: (x[1], x[0]))
	assign_list = map(lambda x: "{:>{w}}".format(f"'{x[0]}' = {x[1]}", w = max_var_len), assign_list)

	max_width = 70

	first = True
	for a in assign_list:
		if len(assign_lines[-1]) >= max_width:
			assign_lines.append(9 * ' ')
			first = True

		if not first:
			assign_lines[-1] += ";  "

		first = False
		assign_lines[-1] += a

	first = True
	spill_lines: List[str] = ["spills:  "]

	if len(spills) == 0:
		spill_lines[0] += "<none>"

	for s in sorted(spills):
		if len(spill_lines[-1]) >= max_width:
			spill_lines.append(9 * ' ')
			first = True

		if not first:
			spill_lines[-1] += ", "

		first = False
		spill_lines[-1] += f"'{s}'"

	return assign_lines, spill_lines


