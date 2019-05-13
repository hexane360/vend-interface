#!/bin/bash
basedir=$(dirname "$(readlink -f "${BASH_SOURCE[0]}")")
pushd $basedir

if [[ $1 == "-s" || $1 == "--server" ]]; then
	#run (auto-updating) doc server
	./venv/bin/python3 -m pdoc --http localhost:8080 vendmachine
else
	#write to 'docs' directory
	export PYTHONWARNINGS='error::UserWarning' #doc warnings -> errors
	./venv/bin/python3 -m pdoc --html --force --output-dir docs vendmachine
fi

echo Exited with code $?
#if [ $? -ne 0 ]; then
