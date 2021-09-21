#!/usr/bin/env python

from __future__ import annotations
from typing import *

from . import ast

from .lexer import *
from .util import StringView

class ParserState:
	def __init__(self, filename: str, s: StringView):
		self.stream: StringView = s
		self.loc: Location = Location(filename, 0, 0)

	def peek(self) -> Token:
		s = self.stream
		l = self.loc
		while True:
			tok, s, l = read_token(s, l)
			if tok.type != "Comment":
				return tok

	def next(self) -> Token:
		while True:
			tok, rest, l = read_token(self.stream, self.loc)
			self.stream = rest
			self.loc = l
			if tok.type != "Comment":
				return tok

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


def is_typename(tok: Token) -> bool:
	return tok.type in ["kw_Int", "kw_Bool", "kw_Void", "kw_String", "ClassName"]


def parse_if_stmt(ps: ParserState) -> ast.IfStmt:
	raise NotImplementedError()

def parse_while_loop(ps: ParserState) -> ast.WhileLoop:
	raise NotImplementedError()

def parse_readln(ps: ParserState) -> ast.ReadLnCall:
	raise NotImplementedError()

def parse_println(ps: ParserState) -> ast.PrintLnCall:
	raise NotImplementedError()

def parse_return_stmt(ps: ParserState) -> ast.ReturnStmt:
	raise NotImplementedError()




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
		# TODO: assigns, calls
		raise ParseException(ps.loc, f"unexpected token '{tok.text}'")


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
		raise ParseException(ps.loc,
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
			ty, name = parse_typed_name(ps)
			var_decls.append(ast.VarDecl(name, ty))
			ps.expect("Semicolon", lambda _: "expected ';' after variable declaration")
		else:
			stmts = parse_stmt_list(ps)

	ps.expect("RBrace")
	return var_decls, stmts


def parse_arg_list(ps: ParserState) -> List[ast.VarDecl]:
	ps.expect("LParen")

	ret: List[ast.VarDecl] = []
	while not ps.empty() and ps.peek().type != "RParen":
		ty, name = parse_typed_name(ps)
		ret.append(ast.VarDecl(name, ty))

		if ps.peek().type == "RParen":
			break
		elif ps.peek().type == "Comma":
			ps.next()
		else:
			raise ParseException(ps.loc, f"unexpected token '{ps.peek().text}'")

	ps.expect("RParen")
	return ret


def parse_class(ps: ParserState, is_first: bool) -> ast.ClassDefn:
	ps.expect("kw_class")
	cls_name = ps.expect("ClassName").text
	cls_def = ast.ClassDefn(cls_name, [], [])

	ps.expect("LBrace")
	if is_first:
		ps.expect("kw_Void", lambda t: f"first method of first class ('main') must return 'Void', not '{t.text}'")
		ps.expect("kw_main", lambda t: f"first method of first class must be named 'main', not '{t.text}'")

		arg_list = parse_arg_list(ps)
		var_decls, stmts = parse_method_body(ps)

		ps.expect("RBrace")

		cls_def.methods.append(ast.MethodDefn("main", cls_def, arg_list, "Void", var_decls, ast.Block(stmts)))
		return cls_def


	# else: normal class
	# since both method and variables start with <Type> <identifier>,
	# defer constructing the AST node till we reach the next token, which should be ';' for a field
	# and '(' for a method.
	while not ps.empty() and ps.peek().type != "RBrace":
		ty, name = parse_typed_name(ps)

		if ps.peek().type == "Semicolon":
			cls_def.fields.append(ast.VarDecl(name, ty))
			ps.next()

		elif ps.peek().type == "LParen":
			arg_list = parse_arg_list(ps)
			var_decls, stmts = parse_method_body(ps)
			cls_def.methods.append(ast.MethodDefn(name, cls_def, arg_list, ty, var_decls, ast.Block(stmts)))

		else:
			raise ParseException(ps.loc,
				f"expected ';' to declare a field or '(' to begin a method, found '{ps.peek().text}' instead")

	ps.expect("RBrace")
	return cls_def


def parse_program(ps: ParserState) -> ast.Program:
	classes: List[ast.ClassDefn] = []
	while not ps.empty():
		classes.append(parse_class(ps, is_first = len(classes) == 0))

	return ast.Program(classes)

