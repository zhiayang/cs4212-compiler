#/usr/bin/env python

from __future__ import annotations
from typing import *
from copy import *
from functools import reduce

from . import ast
from . import ir3

from .util import Location, TCException, StringView, print_warning

class FuncType:
	def __init__(self, clsname: str, params: List[str], ret: str):
		self.clsname: str = clsname
		self.params: List[str] = params
		self.retty: str = ret

	def __str__(self) -> str:
		return f"{self.retty} ({', '.join(self.params)})"

	def __eq__(self, other: object) -> bool:
		if isinstance(other, FuncType):
			# note: don't check return types, you can't overload on that
			return other.clsname == self.clsname and other.params == self.params
		else:
			return False

def get_method_type(method: ast.MethodDefn) -> FuncType:
	return FuncType(method.parent.name, list(map(lambda a: a.type, method.args)), method.return_type)

def mangle_one(name: str) -> str:
	if name == "Void":
		return "v"
	elif name == "Int":
		return "i"
	elif name == "Bool":
		return "b"
	elif name == "String":
		return "s"
	else:
		return f"{len(name)}{name}"

def mangle_name(base: str, type: FuncType) -> str:
	if base == "main":
		return "main"
	return f"_J{mangle_one(type.clsname)}_{mangle_one(base)}{''.join(map(mangle_one, type.params))}E"


class TypecheckState:
	def __init__(self):
		self.class_decls: Dict[str, ast.ClassDefn] = dict()
		self.func_decls: Dict[str, Dict[str, List[FuncType]]] = dict()

		self.classes: Dict[str, ir3.ClassDefn] = dict()
		# stack<map<name, (decl, is_field)>>
		self.varstack: List[Dict[str, Tuple[ir3.VarDecl, bool]]] = []
		self.tmpvars: Dict[str, ir3.VarDecl] = dict()
		self.label_num = 0

		# we have no nested functions, so a single value is sufficient.
		self.current_fn_type: Union[None, FuncType] = None

	def get_new_label(self) -> str:
		self.label_num += 1
		return f".L{self.label_num}"


	def declare_class(self, cls: ast.ClassDefn):
		if cls.name in self.class_decls:
			raise TCException(cls.loc, f"duplicate definition of class '{cls.name}'")

		self.class_decls[cls.name] = cls

	def declare_func(self, fn: ast.MethodDefn):
		if self.func_decls.get(fn.parent.name) is None:
			self.func_decls[fn.parent.name] = dict()

		methods = self.func_decls[fn.parent.name]
		if methods.get(fn.name) is None:
			methods[fn.name] = []

		mt = get_method_type(fn)
		if mt in methods[fn.name]:
			raise TCException(fn.loc, f"duplicate overload '{mt}' for method '{fn.parent.name}::{fn.name}'")

		methods[fn.name].append(get_method_type(fn))

	def add_class(self, cls: ir3.ClassDefn):
		if cls.name in self.classes:
			raise TCException(cls.loc, f"duplicate definition of class '{cls.name}'")

		self.classes[cls.name] = cls

	def enter_function(self, fn: FuncType):
		self.current_fn_type = fn


	def is_valid_type(self, name: str) -> bool:
		return name in ["Int", "String", "Bool", "Void"] or name in self.class_decls

	def is_object_type(self, name: str) -> bool:
		return self.is_valid_type(name) and (name not in ["Int", "Bool", "Void"])

	def get_var(self, loc: Location, name: str) -> Tuple[ir3.VarDecl, bool]:
		if (tmpdecl := self.tmpvars.get(name)) is not None:
			return (tmpdecl, False)

		for vars in reversed(self.varstack):
			if (v := vars.get(name)) is not None:
				return v

		raise TCException(loc, f"variable '{name}' does not exist")

	def add_var(self, var: ir3.VarDecl, is_field: bool):
		if len(self.varstack) == 0:
			raise TCException(var.loc, f"no scope to add variable '{var.name}' into")

		if var.name in self.varstack[-1]:
			raise TCException(var.loc, f"variable '{var.name}' already exists in the current scope")

		self.varstack[-1][var.name] = (var, is_field)

	def get_class_decl(self, loc: Location, name: str) -> ast.ClassDefn:
		if name not in self.class_decls:
			raise TCException(loc, f"class '{name}' does not exist")

		return self.class_decls[name]


	def get_value_type(self, value: ir3.Value) -> str:
		if isinstance(value, ir3.ConstantInt):
			return "Int"
		elif isinstance(value, ir3.ConstantBool):
			return "Bool"
		elif isinstance(value, ir3.ConstantString):
			return "String"
		elif isinstance(value, ir3.ConstantNull):
			return "$NullObject"
		elif isinstance(value, ir3.VarRef):
			return self.get_var(value.loc, value.name)[0].type
		else:
			raise TCException(value.loc, "unknown ir3.Value kind")

	def is_compatible_assignment(self, target_ty: str, value_ty: str) -> bool:
		return (target_ty == value_ty) or (value_ty == "$NullObject" and self.is_object_type(target_ty))


	def push_scope(self) -> None:
		self.varstack.append(dict())

	def pop_scope(self) -> None:
		self.varstack.pop()

	def reset_tmps(self) -> None:
		self.tmpvars.clear()

	def make_temp(self, loc: Location, ty: str) -> ir3.VarDecl:
		assert self.is_valid_type(ty)
		n = f"_t{len(self.tmpvars)}"
		v = ir3.VarDecl(loc, n, ty)
		self.tmpvars[n] = v
		return v


def find_overload(ts: TypecheckState, arg_types: List[str], overloads: List[FuncType]) -> Union[FuncType, None]:

	def check_one_overload(ts: TypecheckState, args: List[str], overload: List[str]) -> bool:
		if len(args) != len(overload):
			return False

		for i in range(0, len(arg_types)):
			if not ts.is_compatible_assignment(overload[i], arg_types[i]):
				return False

		return True


	for overload in overloads:
		if check_one_overload(ts, arg_types, overload.params):
			return overload

	return None






def typecheck_unaryop(ts: TypecheckState, un: ast.UnaryOp) -> Tuple[List[ir3.Stmt], ir3.Value]:
	stmts, value = typecheck_expr(ts, un.expr)

	if un.op not in ["-", "!"]:
		raise TCException(un.loc, f"unknown unary operator '{un.op}'")

	vty = ts.get_value_type(value)
	if (un.op == "-" and vty != "Int") or (un.op == "!" and vty != "Bool"):
		raise TCException(un.loc, f"invalid unary operator '{un.op}' on non-{'Bool' if un.op == '!' else 'Int'} type '{vty}'")

	tmp = ts.make_temp(un.loc, vty)
	expr = ir3.UnaryOp(un.loc, un.op, value)
	stmts.append(ir3.AssignOp(un.loc, tmp.name, expr))
	return (stmts, ir3.VarRef(un.loc, tmp.name))



def typecheck_binaryop(ts: TypecheckState, bi: ast.BinaryOp) -> Tuple[List[ir3.Stmt], ir3.Value]:
	s1, v1 = typecheck_expr(ts, bi.lhs)
	s2, v2 = typecheck_expr(ts, bi.rhs)

	t1 = ts.get_value_type(v1)
	t2 = ts.get_value_type(v2)

	if bi.op not in ["+", "-", "*", "/", "&&", "||", "==", "!=", ">", "<", ">=", "<="]:
		raise TCException(bi.loc, f"unknown unary operator '{bi.op}'")

	if t1 != t2:
		raise TCException(bi.loc, f"incompatible types '{t1}' and '{t2}' for operator '{bi.op}'")

	allowables = {
		"Int": ["+", "-", "*", "/", "==", "!=", ">", "<", ">=", "<="],
		"Bool": ["&&", "||"],
		"String": ["+"]
	}

	if (allowed := allowables.get(t1)) is None or (bi.op not in allowed):
		raise TCException(bi.loc, f"operator '{bi.op}' cannot be applied on arguments of type '{t1}'")

	if bi.op in ["+", "-", "*", "/", "&&", "||"]:
		result = t1
	else:
		result = "Bool"

	tmp = ts.make_temp(bi.loc, result)
	binop = ir3.BinaryOp(bi.loc, v1, bi.op, v2)

	stmts = s1 + s2
	stmts.append(ir3.AssignOp(bi.loc, tmp.name, binop))
	return (stmts, ir3.VarRef(bi.loc, tmp.name))


def typecheck_call(ts: TypecheckState, cls_name: str, this_name: str, call: ast.FuncCall) -> Tuple[List[ir3.Stmt], ir3.Value]:
	# use a slightly different approach, by looking up
	# the func decls in the ts.
	if not isinstance(call.func, ast.VarRef):
		raise TCException(call.loc, f"unknown expression '{call.func}' in function call")

	func_name = call.func.name
	if (methods := ts.func_decls[cls_name].get(func_name)) is None:
		raise TCException(call.loc, f"class '{cls_name}' has no method named '{func_name}'")

	stmts: List[ir3.Stmt] = []

	# now we have the methods, we need to check the overload set with the argument types.
	arg_vals = []
	arg_types = []
	for arg in call.args:
		ss, vl = typecheck_expr(ts, arg)
		arg_types.append(ts.get_value_type(vl))
		arg_vals.append(vl)
		stmts.extend(ss)

	overload = find_overload(ts, arg_types, methods)
	if overload is None:
		raise TCException(call.loc, f"method '{func_name}' in class '{cls_name}' has no overload taking arguments '{arg_types}'")

	mangled_name = mangle_name(func_name, overload)

	# insert the 'this' argument.
	arg_vals.insert(0, ir3.VarRef(call.loc, this_name))

	fncall = ir3.FnCallExpr(call.loc, ir3.FnCall(call.loc, mangled_name, arg_vals))
	return_val = ts.make_temp(call.loc, overload.retty)
	stmts.append(ir3.AssignOp(call.loc, return_val.name, fncall))

	return (stmts, ir3.VarRef(call.loc, return_val.name))





def typecheck_dotop(ts: TypecheckState, dot: ast.DotOp) -> Tuple[List[ir3.Stmt], ir3.Value]:
	stmts, left = typecheck_expr(ts, dot.lhs)
	left_ty = ts.get_value_type(left)

	if not ts.is_object_type(left_ty) or left_ty == "String":
		raise TCException(dot.loc, f"value of type '{left_ty}' does not have any fields or methods")

	# ok, now get the class
	cls = ts.get_class_decl(dot.loc, left_ty)

	# we need a temp for the lhs
	this = ts.make_temp(dot.lhs.loc, left_ty)
	stmts.append(ir3.AssignOp(dot.lhs.loc, this.name, ir3.ValueExpr(dot.lhs.loc, left)))

	if isinstance(dot.rhs, ast.VarRef):
		for f in cls.fields:
			if f.name == dot.rhs.name:
				# and a temp for the rhs
				tmp2 = ts.make_temp(dot.rhs.loc, f.type)
				stmts.append(ir3.AssignOp(dot.rhs.loc, tmp2.name, ir3.DotOp(dot.loc, this.name, f.name)))
				return (stmts, ir3.VarRef(dot.rhs.loc, tmp2.name))

		raise TCException(dot.rhs.loc, f"type '{cls.name}' has no field named '{dot.rhs.name}'")

	elif isinstance(dot.rhs, ast.FuncCall):
		s1, v1 = typecheck_call(ts, cls.name, this.name, dot.rhs)
		return (stmts + s1, v1)

	else:
		raise TCException(dot.loc, f"invalid rhs '{dot.rhs}' on dot operator")











# returns any statements required to generate the value for this expression.
def typecheck_expr(ts: TypecheckState, expr: ast.Expr) -> Tuple[List[ir3.Stmt], ir3.Value]:
	if isinstance(expr, ast.UnaryOp):
		return typecheck_unaryop(ts, expr)

	elif isinstance(expr, ast.BinaryOp):
		return typecheck_binaryop(ts, expr)

	elif isinstance(expr, ast.DotOp):
		return typecheck_dotop(ts, expr)

	elif isinstance(expr, ast.VarRef):
		var = ts.get_var(expr.loc, expr.name)
		if var[1]:
			tmp = ts.make_temp(expr.loc, var[0].type)
			return ([ ir3.AssignOp(expr.loc, tmp.name, ir3.DotOp(expr.loc, "this", var[0].name)) ],
				ir3.VarRef(expr.loc, tmp.name))
		else:
			return ([], ir3.VarRef(expr.loc, var[0].name))

	elif isinstance(expr, ast.FuncCall):
		# we know that 'bare' function calls *must* be called on the implicit 'this'
		cls_ty = ts.get_var(expr.loc, "this")[0].type
		return typecheck_call(ts, cls_ty, "this", expr)

	elif isinstance(expr, ast.ParenExpr):
		return typecheck_expr(ts, expr.expr)

	elif isinstance(expr, ast.NewExpr):
		tmp = ts.make_temp(expr.loc, expr.class_name)
		return ([
			ir3.AssignOp(expr.loc, tmp.name, ir3.NewOp(expr.loc, expr.class_name))
		], ir3.VarRef(expr.loc, tmp.name))

	elif isinstance(expr, ast.ThisLit):
		return ([], ir3.VarRef(expr.loc, "this"))

	elif isinstance(expr, ast.IntegerLit):
		return ([], ir3.ConstantInt(expr.loc, expr.value))

	elif isinstance(expr, ast.BooleanLit):
		return ([], ir3.ConstantBool(expr.loc, expr.value))

	elif isinstance(expr, ast.StringLit):
		return ([], ir3.ConstantString(expr.loc, expr.value))

	elif isinstance(expr, ast.NullLit):
		return ([], ir3.ConstantNull(expr.loc))

	else:
		raise TCException(expr.loc, f"unknown expression '{expr}' (type = {type(expr)})")


def typecheck_readln(ts: TypecheckState, stmt: ast.ReadLnCall) -> List[ir3.Stmt]:
	var = ts.get_var(stmt.loc, stmt.var)[0]
	if var.type not in ["Int", "Bool", "String"]:
		raise TCException(stmt.loc, f"'readln' can only take vars of type 'Int', 'Bool', or 'String' -- not '{var.type}'")

	return [ ir3.ReadLnCall(stmt.loc, stmt.var) ]

def typecheck_println(ts: TypecheckState, stmt: ast.PrintLnCall) -> List[ir3.Stmt]:
	stmts, value = typecheck_expr(ts, stmt.expr)
	if (t := ts.get_value_type(value)) not in ["Int", "Bool", "String"]:
		raise TCException(stmt.loc, f"'println' can only print expressions of type 'Int', 'Bool', or 'String' -- not '{t}'")

	stmts.append(ir3.PrintLnCall(stmt.loc, value))
	return stmts


def typecheck_cond(ts: TypecheckState, expr: ast.Expr) -> Tuple[List[ir3.Stmt], ir3.Value]:
	stmts: List[ir3.Stmt] = []
	if isinstance(expr, ast.BinaryOp):
		if expr.op == "&&":
			# it doesn't matter when we call this, as long as the statement lists get
			# inserted in the right place.
			s1, v1 = typecheck_cond(ts, expr.lhs)
			s2, v2 = typecheck_cond(ts, expr.rhs)

			if (t1 := ts.get_value_type(v1)) != "Bool":
				raise TCException(v1.loc, f"expected boolean value on lhs of '&&', got '{t1}' instead")

			if (t2 := ts.get_value_type(v2)) != "Bool":
				raise TCException(v2.loc, f"expected boolean value on rhs of '&&', got '{t2}' instead")

			result = ts.make_temp(expr.loc, "Bool")

			ltrue_block = ir3.Label(expr.lhs.loc, ts.get_new_label())
			rtrue_block = ir3.Label(expr.lhs.loc, ts.get_new_label())
			merge_block = ir3.Label(expr.lhs.loc, ts.get_new_label())

			stmts.extend(s1)
			stmts += [
				ir3.CondBranch(expr.lhs.loc, v1, ltrue_block.name),

				# now in the implicit false case
				ir3.AssignOp(expr.loc, result.name, ir3.ValueExpr(expr.loc, ir3.ConstantBool(expr.loc, False))),
				ir3.Branch(expr.loc, merge_block.name),

				# now in the lhs-true case
				ltrue_block,

			] + s2 + [
				# rhs got generated.
				ir3.CondBranch(expr.rhs.loc, v2, rtrue_block.name),

				# implicit rhs-false case
				ir3.AssignOp(expr.loc, result.name, ir3.ValueExpr(expr.loc, ir3.ConstantBool(expr.loc, False))),
				ir3.Branch(expr.loc, merge_block.name),

				# true case
				rtrue_block,
				ir3.AssignOp(expr.loc, result.name, ir3.ValueExpr(expr.loc, ir3.ConstantBool(expr.loc, True))),

				merge_block
			]

			return (stmts, ir3.VarRef(expr.loc, result.name))

		elif expr.op == "||":
			s1, v1 = typecheck_cond(ts, expr.lhs)
			s2, v2 = typecheck_cond(ts, expr.rhs)

			if (t1 := ts.get_value_type(v1)) != "Bool":
				raise TCException(v1.loc, f"expected boolean value on lhs of '&&', got '{t1}' instead")

			if (t2 := ts.get_value_type(v2)) != "Bool":
				raise TCException(v2.loc, f"expected boolean value on rhs of '&&', got '{t2}' instead")

			result = ts.make_temp(expr.loc, "Bool")

			true_block = ir3.Label(expr.lhs.loc, ts.get_new_label())
			merge_block = ir3.Label(expr.lhs.loc, ts.get_new_label())

			stmts.extend(s1)
			stmts += [
				cast(ir3.Stmt, ir3.CondBranch(expr.lhs.loc, v1, true_block.name)),

				# implicit false-case
			] + s2 + [
				ir3.CondBranch(expr.rhs.loc, v2, true_block.name),

				# implicit false-false case:
				ir3.AssignOp(expr.loc, result.name, ir3.ValueExpr(expr.loc, ir3.ConstantBool(expr.loc, False))),
				ir3.Branch(expr.loc, merge_block.name),

				# true case:
				true_block,
				ir3.AssignOp(expr.loc, result.name, ir3.ValueExpr(expr.loc, ir3.ConstantBool(expr.loc, True))),

				# merge:
				merge_block
			]
			return (stmts, ir3.VarRef(expr.loc, result.name))

	return typecheck_expr(ts, expr)


def typecheck_if(ts: TypecheckState, stmt: ast.IfStmt) -> List[ir3.Stmt]:
	stmts, cv = typecheck_cond(ts, stmt.condition)
	true_stmts = typecheck_block(ts, stmt.true_case)
	else_stmts = typecheck_block(ts, stmt.else_case)

	# TODO: check whether the if statement returns in all branches -- in which case, omit the merge block
	true_label = ir3.Label(stmt.loc, ts.get_new_label())
	else_label = ir3.Label(stmt.loc, ts.get_new_label())
	merge_label = ir3.Label(stmt.loc, ts.get_new_label())

	stmts += [
		ir3.CondBranch(stmt.condition.loc, cv, true_label.name),
		else_label,
	] + else_stmts + [
		ir3.Branch(true_stmts[0].loc, merge_label.name),
		true_label
	] + true_stmts + [
		ir3.Branch(else_stmts[0].loc, merge_label.name),
		merge_label
	]

	return stmts

def typecheck_while(ts: TypecheckState, stmt: ast.WhileLoop) -> List[ir3.Stmt]:
	stmts, cv = typecheck_cond(ts, stmt.condition)
	body_stmts = typecheck_block(ts, stmt.body)

	# TODO: check whether the while loop returns in all branches -- in which case, omit the merge block
	body_label = ir3.Label(stmt.loc, ts.get_new_label())
	merge_label = ir3.Label(stmt.loc, ts.get_new_label())

	# there's no break or continue, so there's no need to keep track of any of that.
	return stmts + [
		ir3.CondBranch(stmt.condition.loc, cv, body_label.name),
		ir3.Branch(body_stmts[0].loc, merge_label.name),
		body_label
	] + body_stmts + [
		merge_label
	]





def typecheck_assign(ts: TypecheckState, stmt: ast.AssignStmt) -> List[ir3.Stmt]:
	# this is analogous to the (Value, Ptr) return in flax, except there's no
	# getelementptr here. in this case, we just manually generate the lhs-left,
	# store it in a temp, (and we know the rhs must be an identifier), then use
	# the IR3 "a.b = c" construction.

	# note that this works (we can just generate the left side of a dotop (eg. in `a.b.c`, `a.b`)
	# normally, because all class types (ie. anything that has fields) are pointers in jlite,
	# so their value is just their address -- no copies or anything involved. all pointer semantics.
	s2, v2 = typecheck_expr(ts, stmt.rhs)

	def ensure_compatible_types(t1: str, t2: str):
		if not ts.is_compatible_assignment(t1, t2):
			raise TCException(stmt.loc, f"incompatible types in assignment (assigning '{t2}' to '{t1}')")


	if isinstance(stmt.lhs, ast.DotOp):
		dot: ast.DotOp = stmt.lhs

		# typecheck the left side of the dotop separately (eg. for `a.b.c = 69`, generate `a.b` first)
		s1, v1 = typecheck_expr(ts, dot.lhs)
		tmp = ts.make_temp(dot.lhs.loc, ts.get_value_type(v1))
		stmts: List[ir3.Stmt] = s1 + [ ir3.AssignOp(tmp.loc, tmp.name, ir3.ValueExpr(tmp.loc, v1)) ] + s2

		if not isinstance(dot.rhs, ast.VarRef):
			raise TCException(stmt.rhs.loc, f"expected identifier on rhs of '.' in assignment")

		# check that the thing on the left has such a field
		field_name = dot.rhs.name
		lhs_ty = ts.get_value_type(v1)

		if not ts.is_object_type(lhs_ty):
			raise TCException(stmt.rhs.loc, f"cannot access field '{field_name}' on non-class type '{lhs_ty}'")

		field_ty: str = ""
		cls = ts.get_class_decl(dot.loc, lhs_ty)
		for f in cls.fields:
			if f.name == field_name:
				field_ty = f.type
				break

		if field_ty == "":
			raise TCException(stmt.rhs.loc, f"type '{cls.name}' has no field named '{field_name}'")

		ensure_compatible_types(field_ty, ts.get_value_type(v2))
		return stmts + [
			ir3.AssignDotOp(stmt.loc, tmp.name, field_name, ir3.ValueExpr(stmt.rhs.loc, v2))
		]

		assert False and "unreachable"

	# normal var = var
	if not isinstance(stmt.lhs, ast.VarRef):
		raise TCException(stmt.rhs.loc, f"expected identifier on lhs in assignment")

	# if the left side is a field, we must emit a "this.field = <expr>" statement instead.s1
	var_name = stmt.lhs.name
	rhs_expr = ir3.ValueExpr(stmt.rhs.loc, v2)

	if (var := ts.get_var(stmt.lhs.loc, var_name))[1]:
		assign: ir3.Stmt = ir3.AssignDotOp(stmt.loc, "this", var_name, rhs_expr)
	else:
		assign = ir3.AssignOp(stmt.loc, var_name, rhs_expr)

	t1 = var[0].type
	t2 = ts.get_value_type(v2)
	ensure_compatible_types(t1, t2)

	return s2 + [ assign ]


def typecheck_return(ts: TypecheckState, stmt: ast.ReturnStmt) -> List[ir3.Stmt]:
	assert ts.current_fn_type is not None
	retty = ts.current_fn_type.retty

	if stmt.value is not None:
		s, v = typecheck_expr(ts, stmt.value)
		if not ts.is_compatible_assignment(retty, (vt := ts.get_value_type(v))):
			raise TCException(v.loc, f"incompatible value in return; function returns '{retty}', value has type '{vt}'")

		return [ ir3.ReturnStmt(stmt.loc, v) ]
	else:
		if retty != "Void":
			raise TCException(stmt.loc, f"invalid void return in function returning '{retty}'")

		return [ ir3.ReturnStmt(stmt.loc, None) ]







# one statement can produce multiple ir3 statements
def typecheck_stmt(ts: TypecheckState, stmt: ast.Stmt) -> List[ir3.Stmt]:
	if isinstance(stmt, ast.ReadLnCall):
		return typecheck_readln(ts, stmt)

	elif isinstance(stmt, ast.PrintLnCall):
		return typecheck_println(ts, stmt)

	elif isinstance(stmt, ast.IfStmt):
		return typecheck_if(ts, stmt)

	elif isinstance(stmt, ast.WhileLoop):
		return typecheck_while(ts, stmt)

	elif isinstance(stmt, ast.AssignStmt):
		return typecheck_assign(ts, stmt)

	elif isinstance(stmt, ast.ReturnStmt):
		return typecheck_return(ts, stmt)

	elif isinstance(stmt, ast.ExprStmt):
		return typecheck_expr(ts, stmt.expr)[0]

	else:
		raise TCException(stmt.loc, f"unhandled statement {type(stmt)}")


def typecheck_block(ts: TypecheckState, block: ast.Block) -> List[ir3.Stmt]:
	return reduce(lambda a, b: a + b, map(lambda s: typecheck_stmt(ts, s), block.stmts))





def convert_to_basic_blocks(ts: TypecheckState, stmts: List[ir3.Stmt]) -> List[ir3.BasicBlock]:
	blocks: List[ir3.BasicBlock] = []
	block_names: Dict[str, ir3.BasicBlock] = {}

	entry = ir3.BasicBlock(".entry", [], None)
	blocks.append(entry)

	current = entry

	exited_block = False
	did_warn = False
	for i in range(0, len(stmts)):
		stmt = stmts[i]

		if isinstance(stmt, ir3.Label):
			if stmt.name in block_names:
				current = block_names[stmt.name]
			else:
				blk = ir3.BasicBlock(stmt.name, [], current)
				current = blk

			# note we don't append 'stmt' to stmts here because... a label is not even a real statement

			# note that the blocks must be in sequential order (due to the dumb fallthrough design of ir3),
			# so we only add to the list of blocks when we encounter the label, even if the block object
			# itself was created earlier by a jump to it.
			blocks.append(current)

			# of course, reset the flag when we go into a new block
			exited_block = False
			did_warn = False
			continue

		# if we're already out of the block, don't do anything with this statement
		# (especially not adding it to the basic block)
		if exited_block:
			if not did_warn and not isinstance(stmt, ir3.Branch):
				print_warning(stmt.loc, f"unreachable statement")
				did_warn = True
			continue

		if isinstance(stmt, ir3.Branch):
			current.stmts.append(stmt)
			exited_block = True

		elif isinstance(stmt, ir3.CondBranch):
			current.stmts.append(stmt)

			# now this requires a bit of finesse. basic blocks are not supposed to fall through, but
			# stupid ir3 does not implement conditional branches "properly" to support that. so, we
			# assume that there is an implicit jump, just by setting the parent of both true and false
			# cases to this block.

			true_blk = ir3.BasicBlock(stmt.label, [], current)

			# don't add a superfluous block. most of the time, our codegen already has a false block
			if i < len(stmts) and isinstance(stmts[i + 1], ir3.Label):
				next_ = cast(ir3.Label, stmts[i + 1])
				else_blk = ir3.BasicBlock(next_.name, [], current)
			else:
				else_blk = ir3.BasicBlock(ts.get_new_label(), [], current)
				blocks.append(else_blk)

			block_names[true_blk.name] = true_blk
			block_names[else_blk.name] = else_blk

			# the current block is now the else block, due to fallthrough.
			current = else_blk
			exited_block = False
			did_warn = False

		elif isinstance(stmt, ir3.ReturnStmt):
			current.stmts.append(stmt)
			exited_block = True

		else:
			current.stmts.append(stmt)

	return blocks
















def typecheck_method(ts: TypecheckState, meth: ast.MethodDefn) -> ir3.FuncDefn:
	ts.push_scope()

	seen = set()

	vars: List[ir3.VarDecl] = []
	params: List[ir3.VarDecl] = []

	# first insert the 'this' argument.
	this = ir3.VarDecl(meth.loc, "this", meth.parent.name)
	params.append(this)
	ts.add_var(this, is_field = False)

	for param in meth.args:
		if param.name in seen:
			raise TCException(param.loc, f"duplicate parameter '{param.name}' in method declaration")
		seen.add(param.name)

		if not ts.is_valid_type(param.type) or param.type == "Void":
			raise TCException(param.loc, f"parameter '{param.name}' has invalid type '{param.type}'")

		t = ir3.VarDecl(param.loc, param.name, param.type)
		ts.add_var(t, is_field = False)
		params.append(t)

	if not ts.is_valid_type(meth.return_type):
		raise TCException(meth.loc, f"return type '{meth.return_type}' is not a valid type")

	# then, another scope for the local variables themselves. it's not specified, but locals
	# should be able to shadow params, (which can shadow class fields), which is why we
	# need the stack.
	ts.push_scope()

	seen.clear()
	for var in meth.vars:
		if var.name in seen:
			raise TCException(var.loc, f"duplicate local variable '{var.name}'")
		seen.add(var.name)

		if not ts.is_valid_type(var.type) or var.type == "Void":
			raise TCException(param.loc, f"local variable '{var.name}' has invalid type '{var.type}'")

		t = ir3.VarDecl(var.loc, var.name, var.type)
		ts.add_var(t, is_field = False)
		vars.append(t)

	method_type = get_method_type(meth)
	ts.enter_function(method_type)

	stmts = typecheck_block(ts, meth.body)

	# whatever vars are in the innermost scope will be a combination of the original vars as well as
	# any temporaries that we need. we need to hoist all tmpvar declarations to the top of the function.
	vars.extend(ts.tmpvars.values())
	ts.tmpvars.clear()

	ts.pop_scope()
	ts.pop_scope()

	blocks = convert_to_basic_blocks(ts, stmts)

	return ir3.FuncDefn(meth.loc, mangle_name(meth.name, method_type), method_type.clsname, params,
		method_type.retty, vars, blocks)











def typecheck_class(ts: TypecheckState, cls: ast.ClassDefn) -> Tuple[ir3.ClassDefn, List[ir3.FuncDefn]]:
	fields: List[ir3.VarDecl] = []
	seen = set()

	for field in cls.fields:
		if field.name in seen:
			raise TCException(field.loc, f"field '{field.name}' already exists in class '{cls.name}'")
		seen.add(field.name)

		if not ts.is_valid_type(field.type):
			raise TCException(field.loc, f"'{field.type}' does not name a valid type")

		elif field.type == "Void":
			raise TCException(field.loc, f"fields cannot have 'Void' type")

		fields.append(ir3.VarDecl(field.loc, field.name, field.type))

	methods: List[ir3.FuncDefn] = []

	clsdefn = ir3.ClassDefn(cls.loc, cls.name, fields)
	ts.add_class(clsdefn)

	# push a scope for the class fields, and add the fields
	ts.push_scope()
	for f in cls.fields:
		ts.add_var(ir3.VarDecl(f.loc, f.name, f.type), is_field = True)

	for meth in cls.methods:
		methods.append(typecheck_method(ts, meth))

	ts.pop_scope()
	return (clsdefn, methods)



def typecheck_program(program: ast.Program) -> ir3.Program:
	classes: List[ir3.ClassDefn] = []
	methods: List[ir3.FuncDefn] = []

	ts: TypecheckState = TypecheckState()

	try:
		# first, declare all classes and their methods so we know all the valid types.
		for cls in program.classes:
			ts.declare_class(cls)
			for meth in cls.methods:
				ts.declare_func(meth)

		for cls in program.classes:
			ir3cls, meths = typecheck_class(ts, cls)
			classes.append(ir3cls)
			methods.extend(meths)

		return ir3.Program(classes, methods)

	except TCException as e:
		e.throw()


