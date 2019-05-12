#!/bin/bash
basedir=$(dirname "$(readlink -f "${BASH_SOURCE[0]}")")
pushd $basedir

./venv/bin/python3 -m vendmachine

echo Exited with code $?
#if [ $? -ne 0 ]; then
