#!/usr/bin/env python
#-*- coding:utf-8 -*-

"""
Exceptions
"""

class ParserError(Exception):
    def __init__(self, node, msg):
        self.node = node
        self.msg = msg

    def __str__(self):
        n = self.node
        output = '%s(%s:%s) => %s' % (n.fname, n.line, n.col, self.msg)
        return output

    def __repr__(self):
        n = self.node
        output = '%s(%s:%s) => %s' % (n.fname, n.line, n.col, self.msg)
        return output

InterpError = ParserError


class LexicalError(Exception):
    def __init__(self, fname, line, col, msg):
        self.fname = fname
        self.line = line
        self.col = col
        self.msg = msg

    def __str__(self):
        output = '%s(%s:%s) => %s' % (self.fname, self.line, self.col, self.msg)
        return output

    def __repr__(self):
        output = '%s(%s:%s) => %s' % (self.fname, self.line, self.col, self.msg)
        return output


class TypeCheckError(Exception):
    def __init__(self, msg):
        self.msg = msg
