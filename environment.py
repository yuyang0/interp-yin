#!/usr/bin/env python
#-*- coding:utf-8 -*-

"""
Environments
"""
from util import *
from ast import *

class Env(object):
    def __init__(self, p):
        self.parent = p
        self.kv_map = {}

    def lookup(self, k):
        if k in self.kv_map:
            return self.kv_map[k]
        elif self.parent:
            return self.parent.lookup(k)
        else:
            return False

    def lookup_local(self, k):
        if k in self.kv_map:
            return self.kv_map[k]
        else:
            return False

    def put(self, k, v):
        self.kv_map[k] = v

    def set(self, k, v):
        if not self.lookup(k):
            fatal('Env.set', str(k), ' is not binded in this env')
        if k in self.kv_map:
            self.kv_map[k] = v
        else:
            self.parent.set(k, v)

    def __str__(self):
        return str(self.kv_map) + str(self.parent)

def build_initial_env():
    e = Env(False)
    e.put('+', Add())
    e.put('-', Sub())
    e.put('*', Mult())
    e.put('/', Div())
    e.put('<', Lt())
    e.put('<=', Lte())
    e.put('>', Gt())
    e.put('>=', Gte())
    e.put('=', Eq())
    e.put('and', And())
    e.put('or', Or())
    e.put('not', Not())

    e.put('print', Print())
    return e


def build_initial_tenv():
    e = Env(False)
    return e


class SymTableError(Exception):
    def __init__(self, msg):
        self.msg = msg

    def __str__(self):
        return self.msg


class SymTable(object):
    """
    Symbol Table
    """
    def __init__(self, parent=None):
        self.parent = parent
        self.table = {}

    def lookup_property_local(self, name, key):
        entry = self.table.get(name, {})
        return entry.get(key)

    def lookup_property(self, name, key):
        val = self.lookup_property_local(name, key)
        if val:
            return val
        elif self.parent:
            return self.parent.lookup_property(name, key)
        else:
            return None

    def lookup_value(self, name):
        return self.lookup_property(name, "value")

    def lookup_type(self, name):
        return self.lookup_property(name, "type")

    def lookup_value_local(self, name):
        return lookup_property_local(name, "value")

    def lookup_type_local(self, name):
        return lookup_property_local(name, "type")

    def put(self, name, k, v):
        entry = self.table.get(name, {})
        entry[k] = v
        self.table[name] = entry

    def put_value(self, name, val):
        self.put(name, "value", val)

    def put_type(self, name, ty):
        self.put(name, "type", ty)

    def set(self, name, k, v):
        if self.lookup_property_local(name, k, v):
            self.table[name][k] = v
        elif self.parent:
            self.parent.set(name, k, v)
        else:
            fatal(name, " ", "is not defined, so you can't assign")

    def set_value(self, name, v):
        self.set(name, "value", v)

    def set_type(self, name, t):
        self.set(name, "type", t)

    def __str__(self):
        return str(self.table) + str(self.parent)

    @staticmethod
    def init_value_table():
        tbl = SymTable()
        tbl.put_value('+', Add())
        tbl.put_value('-', Sub())
        tbl.put_value('*', Mult())
        tbl.put_value('/', Div())
        tbl.put_value('<', Lt())
        tbl.put_value('<=', Lte())
        tbl.put_value('>', Gt())
        tbl.put_value('>=', Gte())
        tbl.put_value('=', Eq())
        tbl.put_value('and', And())
        tbl.put_value('or', Or())
        tbl.put_value('not', Not())

        tbl.put_value('print', Print())
        return tbl

    @staticmethod
    def init_type_table():
        tbl = SymTable()
        tbl.put_value('+', Add())
        tbl.put_value('-', Sub())
        tbl.put_value('*', Mult())
        tbl.put_value('/', Div())
        tbl.put_value('<', Lt())
        tbl.put_value('<=', Lte())
        tbl.put_value('>', Gt())
        tbl.put_value('>=', Gte())
        tbl.put_value('=', Eq())
        tbl.put_value('and', And())
        tbl.put_value('or', Or())
        tbl.put_value('not', Not())

        tbl.put_value('print', Print())
        return tbl
