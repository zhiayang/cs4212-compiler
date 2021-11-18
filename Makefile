# Makefile

.PHONY: lexer parser typecheck compile
.DEFAULT_TARGET: compile

QEMU        := qemu-arm-static

GEM5_OPTS   := --cpu-type=TimingSimpleCPU --l1d_size=64kB --l1i_size=16kB --caches
GEM5_CMD    =  $(GEM5_DIR)/build/ARM/gem5.fast -q -e --stderr-file=/dev/null
GEM5_CMD    += $(GEM5_DIR)/configs/example/se.py $(GEM5_OPTS) --errout=/dev/null -c

ifeq ("$(shell uname)","Darwin")
	ARM_CC      := toolchain/bin/arm-unknown-linux-gnueabihf-gcc
	GEM5_DIR    ?= ../../gem5
else
	ARM_CC      := arm-linux-gnueabihf-gcc
	GEM5_DIR    ?= ~/code/gem5
endif


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
	@python compile.py -O test/01_simple.j
	@$(ARM_CC) -o test/01_simple.out -static test/01_simple.s


gem5: compile
	@$(GEM5_CMD) test/01_simple.out

qemu: compile
	@$(QEMU) test/01_simple.out
