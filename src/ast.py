#/usr/bin/env python

class Expr:
	pass

class Stmt:
	pass

class BinaryOp(Expr):
	pass

class UnaryOp(Expr):
	pass

class VarRef(Expr):
	pass

class FuncCall(Expr, Stmt):
	pass

class NewExpr(Expr):
	pass

class StringLit(Expr):
	pass

class BooleanLit(Expr):
	pass

class IntegerLit(Expr):
	pass

class NullLit(Expr):
	pass

class ThisLit(Expr):
	pass

class DotOp(Expr):
	pass


class ReadLnCall(Stmt):
	pass

class PrintLnCall(Stmt):
	pass

class IfStmt(Stmt):
	pass

class WhileLoop(Stmt):
	pass

class ReturnStmt(Stmt):
	pass

class AssignStmt(Stmt):
	pass

class VarDecl(Stmt):
	pass

class ClassDefn:
	pass

class MethodDefn:
	pass

class Program:
	pass
