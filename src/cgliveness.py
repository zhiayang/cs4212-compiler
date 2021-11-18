#!/usr/bin/env python

from __future__ import annotations
from typing import *
from copy import *

from . import ir3
from . import iropt
from . import cglower
from . import cgpseudo
from .util import Location, TCException, CGException, StringView, print_warning, escape_string


# returns (ins, outs, defs, uses)
def analyse(func: ir3.FuncDefn, all_stmts: List[ir3.Stmt]) -> Tuple[List[Set[str]], List[Set[str]], \
	List[Set[str]], List[Set[str]]]:

	successors = iropt.compute_successors(func)
	predecessors = iropt.compute_predecessors(func)

	ins: List[Set[str]]  = list(map(lambda _: set(), range(0, len(all_stmts))))
	outs: List[Set[str]] = list(map(lambda _: set(), range(0, len(all_stmts))))
	queue: List[int] = list(range(0, len(all_stmts)))

	defs: List[Set[str]] = list(map(lambda s: iropt.get_statement_defs(s), all_stmts))
	uses: List[Set[str]] = list(map(lambda s: iropt.get_statement_uses(s), all_stmts))

	# furthermore, we consider the first statement to define all locals (incl. temporaries) and arguments.
	defs[0].update(map(lambda v: v.name, func.vars))
	defs[0].update(map(lambda v: v.name, func.params))

	while len(queue) > 0:
		n = queue.pop(0)
		stmt = all_stmts[n]

		old_in = copy(ins[n])

		tmp: Set[str] = set()       # stupidest language ever designed
		outs[n] = tmp.union(*map(lambda succ: ins[succ], successors[n]))
		ins[n]  = uses[n].union(outs[n] - defs[n])

		if old_in != ins[n] and n in predecessors:
			queue.extend(predecessors[n])

	return (ins, outs, defs, uses)
