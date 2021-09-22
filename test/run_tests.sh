#!/usr/bin/env bash

for prog in $(find . -iname "prog*.j" | sort); do
	printf  "$(basename $prog) ... "

	if [ -f "parse.py" ]; then
		PARSER_EXEC="parse.py"
	elif [ -f "../parse.py"]; then
		PARSER_EXEC="../parse.py"
	else
		printf "\ncannot find parse.py\n"
		exit 1
	fi
	python $PARSER_EXEC $prog | diff -q $prog.gold - > /dev/null
	if [ $? -ne 0 ]; then
		printf "\x1b[1;31mfailed\x1b[0m\n"
		python $PARSER_EXEC $prog | diff -u $prog.gold -
	else
		printf "\x1b[1;32mpassed\x1b[0m\n"
	fi
done
