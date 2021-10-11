#/usr/bin/env python

from __future__ import annotations
from typing import *
from copy import *
from functools import reduce

from . import ast
from . import ir3

from .util import Location, TCException, StringView

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
		self.varstack: List[Dict[str, ir3.VarDecl]] = []
		self.tmpvars: Dict[str, ir3.VarDecl] = dict()

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



	def is_valid_type(self, name: str) -> bool:
		return name in ["Int", "String", "Bool", "Void"] or name in self.class_decls

	def is_object_type(self, name: str) -> bool:
		return self.is_valid_type(name) and (name not in ["Int", "Bool", "Void"])

	def get_var(self, loc: Location, name: str) -> ir3.VarDecl:
		if (tmpdecl := self.tmpvars.get(name)) is not None:
			return tmpdecl

		for vars in reversed(self.varstack):
			if (v := vars.get(name)) is not None:
				return v

		raise TCException(loc, f"variable '{name}' does not exist")

	def add_var(self, var: ir3.VarDecl):
		if len(self.varstack) == 0:
			raise TCException(var.loc, f"no scope to add variable '{var.name}' into")

		if var.name in self.varstack[-1]:
			raise TCException(var.loc, f"variable '{var.name}' already exists in the current scope")

		self.varstack[-1][var.name] = var

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
			return self.get_var(value.loc, value.name).type
		else:
			raise TCException(value.loc, "unknown ir3.Value kind")



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
			t1 = arg_types[i]
			t2 = overload[i]

			# it's easier to structure this as a true condition
			if (t1 == t2) or (t1 == "$NullObject" and ts.is_object_type(t2)):
				pass
			else:
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

def typecheck_dotop(ts: TypecheckState, dot: ast.DotOp) -> Tuple[List[ir3.Stmt], ir3.Value]:
	stmts, left = typecheck_expr(ts, dot.lhs)
	left_ty = ts.get_value_type(left)

	print(f"lhs = '{dot.lhs}'")
	print(f"left = {left_ty}")

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
		# use a slightly different approach, by looking up
		# the func decls in the ts.
		if not isinstance(dot.rhs.func, ast.VarRef):
			raise TCException(dot.rhs.loc, f"unknown expression '{dot.rhs.func}' in function call")

		func_name = dot.rhs.func.name
		if (methods := ts.func_decls[cls.name].get(func_name)) is None:
			raise TCException(dot.rhs.loc, f"class '{cls.name}' has no method named '{func_name}'")

		# now we have the methods, we need to check the overload set with the argument types.
		arg_vals = []
		arg_types = []
		for arg in dot.rhs.args:
			ss, vl = typecheck_expr(ts, arg)
			arg_types.append(ts.get_value_type(vl))
			arg_vals.append(vl)
			stmts.extend(ss)

		overload = find_overload(ts, arg_types, methods)
		if overload is None:
			raise TCException(dot.rhs.loc, f"method '{func_name}' in class '{cls.name}' has no overload taking arguments '{arg_types}'")

		mangled_name = mangle_name(func_name, overload)

		# insert the 'this' argument.
		arg_vals.insert(0, ir3.VarRef(dot.rhs.loc, this.name))

		call = ir3.FnCallExpr(dot.rhs.loc, ir3.FnCall(dot.rhs.loc, mangled_name, arg_vals))
		return_val = ts.make_temp(dot.loc, overload.retty)
		stmts.append(ir3.AssignOp(dot.loc, return_val.name, call))

		return (stmts, ir3.VarRef(dot.loc, return_val.name))

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
		return ([], ir3.VarRef(expr.loc, ts.get_var(expr.loc, expr.name).name))

	elif isinstance(expr, ast.FuncCall):
		raise TCException(expr.loc, f"call: {expr.func}")

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
	var = ts.get_var(stmt.loc, stmt.var)
	if var.type not in ["Int", "Bool", "String"]:
		raise TCException(stmt.loc, f"'readln' can only take vars of type 'Int', 'Bool', or 'String' -- not '{var.type}'")

	return [ ir3.ReadLnCall(stmt.loc, stmt.var) ]

def typecheck_println(ts: TypecheckState, stmt: ast.PrintLnCall) -> List[ir3.Stmt]:
	stmts, value = typecheck_expr(ts, stmt.expr)
	if (t := ts.get_value_type(value)) not in ["Int", "Bool", "String"]:
		raise TCException(stmt.loc, f"'println' can only print expressions of type 'Int', 'Bool', or 'String' -- not '{t}'")

	stmts.append(ir3.PrintLnCall(stmt.loc, value))
	return stmts




# one statement can produce multiple ir3 statements
def typecheck_stmt(ts: TypecheckState, stmt: ast.Stmt) -> List[ir3.Stmt]:
	if isinstance(stmt, ast.ReadLnCall):
		return typecheck_readln(ts, stmt)
	elif isinstance(stmt, ast.PrintLnCall):
		return typecheck_println(ts, stmt)

	return []






def typecheck_method(ts: TypecheckState, meth: ast.MethodDefn) -> ir3.FuncDefn:
	ts.push_scope()

	seen = set()

	vars: List[ir3.VarDecl] = []
	params: List[ir3.VarDecl] = []

	# first insert the 'this' argument.
	this = ir3.VarDecl(meth.loc, "this", meth.parent.name)
	params.append(this)
	ts.add_var(this)

	for param in meth.args:
		if param.name in seen:
			raise TCException(param.loc, f"duplicate parameter '{param.name}' in method declaration")
		seen.add(param.name)

		if not ts.is_valid_type(param.type) or param.type == "Void":
			raise TCException(param.loc, f"parameter '{param.name}' has invalid type '{param.type}'")

		t = ir3.VarDecl(param.loc, param.name, param.type)
		params.append(t)
		ts.add_var(t)

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
		vars.append(t)
		ts.add_var(t)

	stmts: List[ir3.Stmt] = reduce(lambda a, b: a + b, map(lambda s: typecheck_stmt(ts, s), meth.body.stmts))

	# whatever vars are in the innermost scope will be a combination of the original vars as well as
	# any temporaries that we need. we need to hoist all tmpvar declarations to the top of the function.
	vars.extend(ts.tmpvars.values())

	ts.pop_scope()
	ts.pop_scope()
	return ir3.FuncDefn(meth.loc, mangle_name(meth.name, get_method_type(meth)), meth.parent.name,
		params, meth.return_type, vars, stmts)











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
		ts.add_var(ir3.VarDecl(f.loc, f.name, f.type))

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
