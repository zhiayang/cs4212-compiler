# Makefile

.PHONY: lexer parser typecheck compile
.DEFAULT_TARGET: compile

lexer:
	@mypy lex.py
	@python lex.py test/e1.j

parser:
	@mypy parse.py
	@python parse.py test/prog6.j

typecheck:
	@mypy gen.py
	@python gen.py test/prog1.j

compile:
	@mypy compile.py
	@python compile.py test/01_simple.j
	@arm-linux-gnueabihf-gcc -o test/01_simple -static test/01_simple.s
	@qemu-arm-static test/01_simple
