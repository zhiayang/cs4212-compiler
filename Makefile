# Makefile

.PHONY: lexer

lexer:
	@mypy lex.py
	@python lex.py test/e1.j

parser:
	@mypy parse.py
	@python parse.py test/prog6.j

typecheck:
	@mypy gen.py
	@python gen.py test/f_overload1.j
