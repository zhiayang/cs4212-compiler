#!/usr/bin/env python

from __future__ import annotations
from typing import *
from copy import *

from . import ast

from .lexer import *
from .util import StringView, print_warning

class ParserState:
	def __init__(self, filename: str, s: StringView):
		self.stream: StringView = s
		self.loc: Location = Location(filename, 0, 0)

	def peek(self) -> Token:
		s = self.stream.clone()
		l = deepcopy(self.loc)
		while True:
			tok, s, l = read_token(s, l)
			if tok.type != "Comment":
				return tok

	def next(self) -> Token:
		while True:
			tok, self.stream, self.loc = read_token(self.stream, self.loc)
			if tok.type != "Comment":
				return tok

	def next_if(self, tok_type: str) -> Optional[Token]:
		if self.peek().type == tok_type:
			return self.next()
		else:
			return None

	def skip_whitespace(self) -> None:
		self.stream, self.loc = eat_whitespace(self.stream, self.loc)

	def empty(self) -> bool:
		return self.peek().type == "EOF"

	def expect(self, tok_type: str, get_msg: Union[str, Callable[[Token], str]] = None) -> Token:
		tok = self.next()
		if tok.type != tok_type:
			if get_msg is None:
				tok_type_str = tok_type[3:] if tok_type.startswith('kw_') else tok_type
				if self.empty():
					raise ParseException(self.loc, f"unexpected end of input; expected '{tok_type_str}'")
				else:
					raise ParseException(self.loc, f"expected '{tok_type_str}', found '{tok.text}' instead")

			elif isinstance(get_msg, str):
				raise ParseException(self.loc, get_msg)

			else:
				raise ParseException(self.loc, get_msg(tok))
		else:
			return tok

	def expect_semicolon(self):
		old_loc = self.loc
		if (tok := self.next()).type != "Semicolon":
			if self.empty():
				raise ParseException(old_loc, f"unexpected end of input; expected ';' after statement")
			else:
				raise ParseException(old_loc, f"expected ';' after statement")


def is_typename(tok: Token) -> bool:
	return tok.type in ["kw_Int", "kw_Bool", "kw_Void", "kw_String", "ClassName"]

def get_precedence(tok: Token) -> int:
	if tok.type in ["Asterisk", "Slash"]:
		return 69
	elif tok.type in ["Plus", "Minus"]:
		return 68
	elif tok.type in ["LAngle", "RAngle", "LessThanEqual", "GreaterEqual", "EqualsTo", "NotEqual"]:
		return 67
	elif tok.type == "LogicalAnd":
		return 66
	elif tok.type == "LogicalOr":
		return 65
	else:
		return -1


# expects the head to be '('
def parse_func_call(ps: ParserState, callee: ast.Expr) -> ast.FuncCall:
	ps.expect("LParen", f"expected '(' for function call")

	arg_list: List[ast.Expr] = []
	while not ps.empty() and ps.peek().type != "RParen":
		arg_list.append(parse_expr(ps))

		if ps.peek().type == "RParen":
			break
		elif ps.next_if("Comma"):
			pass
		else:
			raise ParseException(ps.loc, f"unexpected token '{ps.peek().text}'")

	ps.expect("RParen")
	return ast.FuncCall(callee.loc, callee, arg_list)


def parse_atom_chain(ps: ParserState, lhs: ast.Expr) -> ast.Expr:
	if tok := ps.next_if("Period"):
		ident = ps.expect("Identifier", f"expected identifier after '.'")

		rhs: ast.Expr
		if ps.peek().type == "LParen":
			rhs = parse_func_call(ps, ast.VarRef(ident.loc, ident.text))
		else:
			rhs = ast.VarRef(ident.loc, ident.text)

		return parse_atom_chain(ps, ast.DotOp(tok.loc, lhs, rhs))

	elif ps.peek().type == "LParen":
		return parse_func_call(ps, lhs)
	else:
		return lhs


def parse_primary(ps: ParserState) -> ast.Expr:
	if tok := ps.next_if("kw_true"):
		return ast.BooleanLit(tok.loc, True)

	elif tok := ps.next_if("kw_false"):
		return ast.BooleanLit(tok.loc, False)

	elif tok := ps.next_if("kw_null"):
		return ast.NullLit(tok.loc)

	elif tok := ps.next_if("kw_this"):
		return ast.ThisLit(tok.loc)

	elif (str_lit := ps.next_if("StringLiteral")):
		return ast.StringLit(str_lit.loc, str_lit.text)

	elif (int_lit := ps.next_if("IntegerLiteral")):
		return ast.IntegerLit(int_lit.loc, int(int_lit.text))

	elif tok := ps.next_if("kw_new"):
		cls_name = ps.expect("ClassName", "expected class name after 'new'").text
		ps.expect("LParen")
		ps.expect("RParen")

		new = ast.NewExpr(tok.loc, cls_name)
		if ps.peek().type == "Period":
			return parse_atom_chain(ps, new)
		else:
			return new

	elif ps.next_if("LParen"):
		inside: ast.Expr = parse_expr(ps)
		ps.expect("RParen")
		return ast.ParenExpr(inside)

	elif (var_name := ps.next_if("Identifier")):
		vr = ast.VarRef(var_name.loc, var_name.text)
		return parse_atom_chain(ps, vr)

	else:
		raise ParseException(ps.loc, f"unexpected token '{ps.peek().text}' in expression")



def parse_unary(ps: ParserState) -> ast.Expr:
	if tok := ps.next_if("Exclamation"):
		return ast.UnaryOp(tok.loc, parse_unary(ps), '!')

	elif tok := ps.next_if("Minus"):
		return ast.UnaryOp(tok.loc, parse_unary(ps), '-')

	else:
		return parse_primary(ps)




def parse_rhs(ps: ParserState, lhs: ast.Expr, prio: int) -> ast.Expr:
	if ps.empty():
		return lhs

	while True:
		if ps.peek().type == "Period":
			lhs = parse_atom_chain(ps, lhs)
			continue

		prec: int = get_precedence(ps.peek())
		if prec < prio:
			return lhs

		ps.skip_whitespace()
		op_loc = ps.loc
		op: str = ps.next().text

		rhs = parse_unary(ps)

		# note: there is no right-associative operator here, so this works fine without special-casing that
		next: int = get_precedence(ps.peek())
		if next > prec:
			rhs = parse_rhs(ps, rhs, prec + 1)

		lhs = ast.BinaryOp(op_loc, lhs, rhs, op)


def parse_expr(ps: ParserState) -> ast.Expr:
	return parse_rhs(ps, parse_unary(ps), 0)



def parse_stmt_list(ps: ParserState) -> List[ast.Stmt]:
	stmts: List[ast.Stmt] = []
	while not ps.empty():
		# while not strictly necessary, check for a typename here and give a nicer error message
		if is_typename(ps.peek()):
			raise ParseException(ps.loc, "variable declarations must be at the top of the method body")

		elif ps.peek().type == "RBrace":
			break;

		stmts.append(parse_stmt(ps))

	return stmts


def parse_block(ps: ParserState) -> ast.Block:
	ps.expect("LBrace", "expected '{' to start a block")
	stmts = parse_stmt_list(ps)
	ps.expect("RBrace", "expected '}' to end a block")
	return ast.Block(stmts)


def parse_if_stmt(ps: ParserState) -> ast.IfStmt:
	loc = ps.expect("kw_if").loc
	ps.expect("LParen", lambda t: f"expected '(' after 'if', found '{t.text}' instead")

	condition = parse_expr(ps)

	ps.expect("RParen", lambda t: f"expected ')' after if condition, found '{t.text}' instead")

	true_case = parse_block(ps)
	if len(true_case.stmts) == 0:
		raise ParseException(ps.loc, "if statement must contain at least one statement")

	ps.expect("kw_else", "'else' clause is mandatory in if statements")

	else_case = parse_block(ps)
	if len(else_case.stmts) == 0:
		raise ParseException(ps.loc, "if statement (else branch) must contain at least one statement")

	return ast.IfStmt(loc, condition, true_case, else_case)



def parse_while_loop(ps: ParserState) -> ast.WhileLoop:
	loc = ps.expect("kw_while").loc
	ps.expect("LParen", lambda t: f"expected '(' after 'while', found '{t.text}' instead")

	condition = parse_expr(ps)

	ps.expect("RParen", lambda t: f"expected ')' after while condition, found '{t.text}' instead")

	# while loops can have an empty body... for some reason.
	body = parse_block(ps)
	return ast.WhileLoop(loc, condition, body)


def parse_readln(ps: ParserState) -> ast.ReadLnCall:
	loc = ps.expect("kw_readln").loc
	ps.expect("LParen", lambda t: f"expected '(' after 'readln', found '{t.text}' instead")

	ident = ps.expect("Identifier", "expected identifier in argument to 'readln'").text

	ps.expect("RParen")
	ps.expect_semicolon()
	return ast.ReadLnCall(loc, ident)

def parse_println(ps: ParserState) -> ast.PrintLnCall:
	loc = ps.expect("kw_println").loc
	ps.expect("LParen", lambda t: f"expected '(' after 'println', found '{t.text}' instead")

	ret = ast.PrintLnCall(loc, parse_expr(ps))
	ps.expect("RParen")
	ps.expect_semicolon()
	return ret

def parse_return_stmt(ps: ParserState) -> ast.ReturnStmt:
	loc = ps.expect("kw_return").loc

	if ps.next_if("Semicolon"):
		return ast.ReturnStmt(loc, None)

	expr = parse_expr(ps)
	ps.expect_semicolon()

	return ast.ReturnStmt(loc, expr)





def parse_stmt(ps: ParserState) -> ast.Stmt:
	tok: Token = ps.peek()

	if tok.type == "kw_if":
		return parse_if_stmt(ps)

	elif tok.type == "kw_while":
		return parse_while_loop(ps)

	elif tok.type == "kw_readln":
		return parse_readln(ps)

	elif tok.type == "kw_println":
		return parse_println(ps)

	elif tok.type == "kw_return":
		return parse_return_stmt(ps)

	else:
		# this is a little weird, but for normal languages where expressions
		# are statements in-and-of-themselves, we would be parsing a statement here.
		# so do that, but only allow certain kinds of expressions, namely calls and assigns.
		expr: ast.Expr = parse_expr(ps)

		# if this is an assignment, do it directly.
		if tmp := ps.next_if("Equal"):
			if not isinstance(expr, ast.DotOp) and not isinstance(expr, ast.VarRef):
				raise ParseException(expr.loc, "left-hand operand of assignment must be an identifier or a dotop")

			elif isinstance(expr, ast.DotOp) and isinstance(expr.rhs, ast.FuncCall):
				raise ParseException(expr.loc, "cannot assign to a function call")

			assign = ast.AssignStmt(tmp.loc, expr, parse_expr(ps));
			ps.expect_semicolon()
			return assign


		ps.expect_semicolon()
		if isinstance(expr, ast.FuncCall) or (isinstance(expr, ast.DotOp) and isinstance(expr.rhs, ast.FuncCall)):
			return ast.ExprStmt(expr)

		# here we'd raise the error on the semicolon, which i think is fine...
		raise ParseException(ps.loc, "expressions are not statements")



def parse_typed_name(ps: ParserState) -> Tuple[str, str]:
	"""parses 'Type identifier'"""
	ty: str = ""
	name: str = ""

	tok = ps.next()
	if tok.type == "kw_Int":      ty = "Int"
	elif tok.type == "kw_Bool":   ty = "Bool"
	elif tok.type == "kw_Void":   ty = "Void"
	elif tok.type == "kw_String": ty = "String"
	elif tok.type == "ClassName": ty = tok.text
	else:
		raise ParseException(tok.loc,
			f"expected typename (either 'Int', 'Void', 'Bool', 'String', or a class name), found '{tok.text}' instead")

	name = ps.expect("Identifier").text

	assert len(name) > 0 and len(ty) > 0
	return ty, name


def parse_method_body(ps: ParserState) -> Tuple[List[ast.VarDecl], List[ast.Stmt]]:
	ps.expect("LBrace")

	# var decls must come before statements like it's 1989.
	# we know that statements never start with a class name, so we use that to differentiate.
	var_decls: List[ast.VarDecl] = []
	stmts: List[ast.Stmt] = []

	while not ps.empty() and ps.peek().type != "RBrace":
		if is_typename(ps.peek()):
			ps.skip_whitespace()

			loc = ps.loc
			ty, name = parse_typed_name(ps)
			var_decls.append(ast.VarDecl(loc, name, ty))
			ps.expect("Semicolon", "expected ';' after variable declaration")
		else:
			stmts = parse_stmt_list(ps)

	if len(stmts) == 0:
		raise ParseException(ps.loc, "method body cannot be empty")

	ps.expect("RBrace")
	return var_decls, stmts


def parse_arg_list(ps: ParserState) -> List[ast.VarDecl]:
	ps.expect("LParen")

	ret: List[ast.VarDecl] = []
	while not ps.empty() and ps.peek().type != "RParen":
		loc = ps.loc
		ty, name = parse_typed_name(ps)
		ret.append(ast.VarDecl(loc, name, ty))

		if ps.peek().type == "RParen":
			break
		elif ps.peek().type == "Comma":
			ps.next()
		else:
			raise ParseException(ps.loc, f"unexpected token '{ps.peek().text}'")

	ps.expect("RParen")
	return ret


def parse_class(ps: ParserState, is_first: bool) -> ast.ClassDefn:
	loc = ps.expect("kw_class").loc
	cls_name = ps.expect("ClassName").text
	cls_def = ast.ClassDefn(loc, cls_name, [], [])

	ps.expect("LBrace")
	if is_first:
		loc = ps.expect("kw_Void", lambda t: f"first method of first class ('main') must return 'Void', not '{t.text}'").loc
		ps.expect("kw_main", lambda t: f"first method of first class must be named 'main', not '{t.text}'")

		arg_list = parse_arg_list(ps)
		var_decls, stmts = parse_method_body(ps)

		ps.expect("RBrace")

		cls_def.methods.append(ast.MethodDefn(loc, "main", cls_def, arg_list, "Void", var_decls, ast.Block(stmts)))
		return cls_def


	# else: normal class
	# since both method and variables start with <Type> <identifier>,
	# defer constructing the AST node till we reach the next token, which should be ';' for a field
	# and '(' for a method.
	while not ps.empty() and ps.peek().type != "RBrace":
		ps.skip_whitespace()

		loc = ps.loc
		ty, name = parse_typed_name(ps)

		if ps.peek().type == "Semicolon":
			cls_def.fields.append(ast.VarDecl(loc, name, ty))
			ps.next()

		elif ps.peek().type == "LParen":
			arg_list = parse_arg_list(ps)
			var_decls, stmts = parse_method_body(ps)
			cls_def.methods.append(ast.MethodDefn(loc, name, cls_def, arg_list, ty, var_decls, ast.Block(stmts)))

		else:
			raise ParseException(ps.loc,
				f"expected ';' to declare a field or '(' to begin a method, found '{ps.peek().text}' instead")

	ps.expect("RBrace")
	return cls_def


def parse_program(ps: ParserState) -> ast.Program:
	classes: List[ast.ClassDefn] = []

	try:
		while not ps.empty():
			classes.append(parse_class(ps, is_first = len(classes) == 0))

		if len(classes) == 0:
			raise ParseException(ps.loc, "at least one class (containing the main method) must be defined")

	except ParseException as e:
		e.throw()

	return ast.Program(classes)

