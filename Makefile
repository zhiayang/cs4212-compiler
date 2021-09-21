# Makefile

.PHONY: lexer

lexer:
	@mypy lex.py
	@python lex.py test/e1.j
