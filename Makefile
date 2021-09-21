# Makefile

.PHONY: lexer

lexer:
	@mypy lex.py
	@python lex.py test/e1.j

parser:
	@mypy parse.py
	@python parse.py test/e.j
