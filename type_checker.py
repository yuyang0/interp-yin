#!/usr/bin/env python
#-*- coding:utf-8 -*-

"""
type checker
"""
from parser import Parser
from util import fatal
from environment import SymTable
from error import ParserError, TypeCheckError
from constants import callstack


class TypeChecker(object):
    def __init__(self, fname):
        self.fname = fname

    def type_check(self):
        p = Parser(self.fname)
        try:
            node = p.parse()
        except ParserError, e:
            ctx = "Traceback: \n"
            for f in callstack:
                ctx = ctx + str(f) + '\n'
            output = ctx + str(e)
            fatal(output)
        tbl = SymTable.init_type_table()
        try:
            return node.interp(tbl)
        except TypeCheckError, e:
            fatal(str(e))
