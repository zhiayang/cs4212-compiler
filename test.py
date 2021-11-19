#!/usr/bin/env python

from __future__ import annotations
from typing import *
from copy import copy

import os
import sys
import subprocess as sub



def replace_ext(s: str, ext: str) -> str:
	return os.path.splitext(s)[0] + ext

def colourise(msg: str, colour: str) -> str:
	if sys.stdout.isatty():
		return f"\x1b[{colour}{msg}\x1b[0m"
	else:
		return msg

def file_exists(path: str) -> bool:
	return os.path.exists(path) and os.path.isfile(path)



def compile_source(compiler: str, source: str, opt: bool) -> Tuple[str, bool]:
	compile_flags = [ os.path.join('.', compiler), "--no-output", source ]
	if opt:
		compile_flags.append("--opt")

	proc = sub.run(compile_flags, stdout=sub.PIPE, stderr=sub.STDOUT, text=True)
	return proc.stdout, proc.returncode == 0


def assemble_file(gcc: str, asm: str, output: str) -> Tuple[str, bool]:
	flags = [ gcc, "-static", "-x", "assembler", "-o", output, "-" ]
	proc = sub.run(flags, stdout=sub.PIPE, stderr=sub.STDOUT, input=asm, text=True)
	return proc.stdout, proc.returncode == 0


def run_compiled_output(gem5: Tuple[str, List[str]], exe: str, stdin: Optional[str]) -> Tuple[str, bool]:
	cmd = [ gem5[0], *gem5[1] ]
	if stdin is not None:
		cmd.append(f"--input={stdin}")

	proc = sub.run([ *cmd, "-c", exe], stdout=sub.PIPE, stderr=sub.STDOUT, text=True)
	output = proc.stdout
	lines = output.splitlines()

	while len(lines) > 0:
		x = lines.pop(0)
		if x == "**** REAL SIMULATION ****":
			break

	if len(lines[-1]) > 0 and lines[-1].startswith("Exiting @ tick"):
		lines.pop(len(lines) - 1)

	return ('\n'.join(lines) + "\n"), proc.returncode == 0



def run_one(compiler: str, gcc_bin: str, gem5: Tuple[str, List[str]], source: str, clean_only = False) -> int:
	print(f"{os.path.basename(source)}: ", end="")


	# check for the required test files
	expected_asm_files = {
		False: replace_ext(source, ".s.gold"),
		True:  replace_ext(source, ".s.opt")
	}

	stdout_file = replace_ext(source, ".stdout")

	if not file_exists(expected_asm_files[True]) or not file_exists(expected_asm_files[False]) or not file_exists(stdout_file):
		print(colourise(f"\tskipped (missing files)", "1;35m"))
		return 0


	expected_asms = { k: open(expected_asm_files[k], "r").read() for k in expected_asm_files }
	expected_stdout  = open(stdout_file, "r").read()

	# delete the out file, if it exists.
	exe_file = replace_ext(source, ".out")

	cleanup = [
		exe_file,
		f"{stdout_file}.actual",
		f"{stdout_file}.opt.actual",
		f"{replace_ext(source, '.s.opt.actual')}",
		f"{replace_ext(source, '.s.gold.actual')}"
	]

	for file in cleanup:
		if file_exists(file):
			os.remove(file)

	if clean_only:
		return 0

	stdin_file: Optional[str] = replace_ext(source, ".stdin")
	if not file_exists(cast(str, stdin_file)):
		stdin_file = None


	def perform(opt: bool) -> bool:
		print(f"    test ({'opt' if opt else 'reg'})  jlite: ", end="", flush=True)

		asm, ok = compile_source(compiler, source, opt)
		if ok:
			print(colourise(f"ok", "1;32m"), end="", flush=True)
		else:
			print(colourise(f"err", "1;31m"), end="", flush=True)
			print("")
			return False

		# compile it, making the exe file by calling gcc.
		print(f" gcc: ", end="", flush=True)
		err, ok = assemble_file(gcc_bin, asm, exe_file)
		if ok:
			print(colourise(f"ok", "1;32m"), end="", flush=True)
		else:
			print(colourise(f"err", "1;31m"), end="", flush=True)
			print(f"    {colourise('>', '1;35m')} {err}")
			return False



		to_see: List[str] = []
		failed = False


		print(f" asm: ", end="", flush=True)


		# check that the asm matches
		expected_asm = expected_asms[opt]
		if asm == expected_asm:
			print(colourise(f"match", "1;32m"), end="", flush=True)
		else:
			print(f"{colourise(f'mismatch', '1;31m')}", end="", flush=True)

			open(f"{expected_asm_files[opt]}.actual", "w").write(asm)
			to_see.append(f"    > see {expected_asm_files[opt]}.actual")

			# don't skip, keep running...
			failed = True


		# run the new process through gem
		out, ok = run_compiled_output(gem5, exe_file, stdin_file)
		print(f" out: ", end="", flush=True)

		if not ok:
			print(f"{colourise(f'error', '1;35m')}")
			failed = True

		elif out == expected_stdout:
			print(colourise(f"match", "1;32m"), end="", flush=True)

		else:
			print(f"{colourise(f'mismatch', '1;31m')}", end="", flush=True)

			open(f"{stdout_file}{'.opt' if opt else ''}.actual", "w").write(out)
			to_see.append(f"    > see {stdout_file}{'.opt' if opt else ''}.actual")
			failed = True

		print("")
		for see in to_see:
			print(see)

		return not failed


	failed = False
	print("")
	for opt in [ False, True ]:
		failed |= not perform(opt)


	return -1 if failed else 1







def get_gem5_cmdline(gem5_bin: str) -> Tuple[str, List[str]]:
	# first get the gem5 directory. the path looks something like this:
	# "<something>/.../gem5/build/ARM/gem5.fast", so we add 3 '..'s to get to 'gem5'
	gem5_dir = os.path.normpath(os.path.join(gem5_bin, "..", "..", ".."))
	if not os.path.exists(gem5_dir) or not os.path.isdir(gem5_dir):
		print(f"could not find gem5 directory: '{gem5_dir}' does not exist (or is not a directory)")
		sys.exit(1)

	gem5_bin = os.path.normpath(gem5_bin)
	return gem5_bin, [
		"-q", "-e", "--stderr-file=/dev/null",
		os.path.join(gem5_dir, "configs", "example", "se.py"),
		"--cpu-type=TimingSimpleCPU",
		"--l1d_size=64kB",
		"--l1i_size=16kB",
		"--caches"
	]

	# ../../gem5/configs/example/se.py --input="asdf" -c ./test/01_simple.out





def main():
	if len(sys.argv) != 5:
		print(f"usage: ./test.py <compile.py> <path-to-gcc> <path-to-gem5> <folder>")
		sys.exit(1)

	if not file_exists(sys.argv[1]):
		print(f"compile.py '{sys.argv[1]}' does not exist (or is not a file)")
		sys.exit(1)

	if not file_exists(sys.argv[2]):
		print(f"gcc '{sys.argv[2]}' does not exist (or is not a file)")
		sys.exit(1)

	if not file_exists(sys.argv[3]):
		print(f"gem5 executable '{sys.argv[3]}' does not exist (or is not a file)")
		sys.exit(1)

	if not os.path.exists(sys.argv[4]) or not os.path.isdir(sys.argv[4]):
		print(f"tests folder '{sys.argv[4]}' does not exist")
		sys.exit(1)


	compiler_bin    = os.path.normpath(sys.argv[1])
	gcc_bin         = sys.argv[2]
	gem5            = get_gem5_cmdline(sys.argv[3])
	tests_folder    = sys.argv[4]

	total = 0
	passed = 0

	for name_ in reversed(sorted(os.listdir(tests_folder))):
		name = os.path.join(tests_folder, name_)
		if os.path.isfile(name) and name.endswith(".j"):
			if (res := run_one(compiler_bin, gcc_bin, gem5, name)) != 0:
				passed += (1 if res > 0 else 0)
				total += 1

	plural = lambda s, n: s if n == 1 else f"{s}s"
	print(f"{passed}/{total} ({100 * passed / max(1, total):.1f}%) {plural('test', passed)} passed, {total - passed} failed")


if __name__ == "__main__":
	main()
