#!/bin/bash
basedir=$(dirname "$(readlink -f "${BASH_SOURCE[0]}")")
pushd $basedir

export PYTHONWARNINGS='error::UserWarning' #doc warnings -> errors

if [[ $1 == "-s" || $1 == "--server" ]]; then
	#run (auto-updating) doc server
	./venv/bin/python3 -m pdoc --http localhost:8080 vendmachine
else
	#write to 'doc' directory
	./venv/bin/python3 -m pdoc --html --force --html-dir doc vendmachine
fi

echo Exited with code $?
#if [ $? -ne 0 ]; then
