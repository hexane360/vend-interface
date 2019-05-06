#!/home/vend/vend-interface/venv/bin/python3

import os
import sys

#get directory of this file
basedir = os.path.dirname(os.path.realpath(__file__))

#add src directory to python's search path
sys.path.insert(0, os.path.join(basedir, "vendmachine"))

import vendmachine
vendmachine.main()
