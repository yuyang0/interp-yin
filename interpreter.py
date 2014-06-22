#!/usr/bin/env python
#-*- coding:utf-8 -*-

"""
interpreter
"""
from parser import Parser
from util import fatal
from environment import build_initial_env
from error import ParserError, InterpError
from constants import *

class Interpreter(object):
    def __init__(self, fname):
        self.fname = fname

    def interp(self):
        p = Parser(self.fname)
        try:
            node = p.parse()
        except ParserError, e:
            ctx = "Traceback: \n"
            for f in callstack:
                ctx = ctx + str(f) + '\n'
            output = ctx + str(e)
            fatal(output)
        e = build_initial_env()
        try:
            return node.interp(e)
        except InterpError, e:
            fatal(str(e))


if __name__ == '__main__':
    import sys
    i = Interpreter(sys.argv[1])
    i.interp()
