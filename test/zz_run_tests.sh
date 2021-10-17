#!/usr/bin/env bash

if [ -f "gen.py" ]; then
	PARSER_EXEC="gen.py"
	DIR="test"
elif [ -f "../gen.py"]; then
	PARSER_EXEC="../gen.py"
	DIR="."
else
	printf "\ncannot find gen.py\n"
	exit 1
fi

for prog in $(find $DIR -maxdepth 1 -iname "*.j" | sort); do
	printf  "%-30s" $(basename $prog)
	if [ ! -f $prog.gold ]; then
		printf "\x1b[1;35mskipped\x1b[0m (no gold file)\n"
		continue
	fi

	python $PARSER_EXEC $prog | diff -q $prog.gold - > /dev/null
	if [ $? -ne 0 ]; then
		printf "\x1b[1;31mfailed\x1b[0m\n"
		python $PARSER_EXEC $prog | diff -u $prog.gold -
	else
		printf "\x1b[1;32mpassed\x1b[0m\n"
	fi
done
