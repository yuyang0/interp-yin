#!/usr/bin/env python
#-*- coding:utf-8 -*-

"""
interpreter
"""
from parser import Parser
from util import fatal
from environment import SymTable
from error import ParserError, InterpError
from constants import callstack


class Interpreter(object):
    def __init__(self, fname, text=None):
        self.fname = fname
        self.text = text

    def interp(self):
        p = Parser(self.fname, self.text)
        try:
            node = p.parse()
        except ParserError, e:
            ctx = "Traceback: \n"
            for f in callstack:
                ctx = ctx + str(f) + '\n'
            output = ctx + str(e)
            fatal(output)
        tbl = SymTable.init_value_table()
        try:
            return node.interp(tbl)
        except InterpError, e:
            fatal(str(e))

    @staticmethod
    def eval(ss):
        i = Interpreter("stdin", ss)
        return i.interp()


def repl():
    while True:
        ss = raw_input("==> ")
        print Interpreter.eval(ss)


if __name__ == '__main__':
    import sys
    if len(sys.argv) == 1:
        import readline
        repl()
    else:
        i = Interpreter(sys.argv[1])
        i.interp()
