#!/usr/bin/python3

import sys, ast

f = open(sys.argv[1], 'r')
print(ast.dump(ast.parse(f.read())))
