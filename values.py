#!/usr/bin/env python
#-*- coding:utf-8 -*-

"""
Expressed Values
"""
import sys

from util import *
from constants import *

class Value(object):
    pass

class BoolValue(Value):
    def __init__(self, val):
        self.value = val

    def __str__(self):
        return str(self.value)

class IntValue(Value):
    def __init__(self, val):
        self.value = val

    def __str__(self):
        return str(self.value)

class FloatValue(Value):
    def __init__(self, val):
        self.value = val

    def __str__(self):
        return str(self.value)

class StrValue(Value):
    def __init__(self, val):
        self.value = val

    def __str__(self):
        return self.value

class VectorValue(Value):
    def __init__(self, vals):
        self.values = vals

    def __str__(self):
        ss = ' '.join(map(str, self.values))
        return VECTOR_BEGIN + ss + VECTOR_END

class RecordLiteralValue(Value):
    def __init__(self, kv_map):
        self.kv_map = kv_map

    def __str__(self):
        ss = ''
        for k in self.kv_map:
            ss = ss + KEYWORD_PREFIX + str(k) + ' ' + str(self.kv_map[k]) + ' '
        return RECORD_BEGIN + ss.strip() + RECORD_END

class Closure(Value):
    def __init__(self, args, properties, body, tbl):
        self.args = args
        self.properties = properties
        self.body = body
        self.tbl = tbl

    def __str__(self):
        return str(self.args) + 'Env: ' + str(self.env)

############ primitive functions ####################
class PrimitiveFun(Value):
    def __init__(self, op, min_arity, max_arity):
        self.op = op
        self.min_arity = min_arity
        self.max_arity = max_arity

    def check_arity(self, n):
        if n >= self.min_arity and n <= self.max_arity:
            return True
        else:
            return False

    def __str__(self):
        return str(self.op)


class Add(PrimitiveFun):
    def __init__(self):
        super(Add, self).__init__('+', 0, sys.maxint)

    def apply(self, args):
        if len(args) == 0:
            return IntValue(0)
        elif len(args) == 1:
            return args
        else:
            has_float = False
            ret = 0
            for arg in args:
                if (not isinstance(arg, IntValue)) and\
                   (not isinstance(arg, FloatValue)):
                    fatal('arguments for + must be integer or float')
                if isinstance(arg, FloatValue):
                    has_float = True
                ret += arg.value
            if has_float:
                return FloatValue(ret)
            else:
                return IntValue(ret)

class Sub(PrimitiveFun):
    def __init__(self):
        super(Sub, self).__init__('-', 1, sys.maxint)

    def apply(self, args):
        has_float = False
        ret = 0
        for i, arg in enumerate(args):
            if (not isinstance(arg, IntValue)) and\
               (not isinstance(arg, FloatValue)):
                fatal('argument for - must be integer or float')
            if isinstance(arg, FloatValue):
                has_float = True
            if i == 0:
                ret = arg.value
            else:
                ret -= arg.value
        if len(args) == 1:      # minus
            ret = -ret

        if has_float:
            return FloatValue(ret)
        else:
            return IntValue(ret)

class Mult(PrimitiveFun):
    def __init__(self):
        super(Mult, self).__init__('*', 0, sys.maxint)

    def apply(self, args):
        if len(args) == 0:
            return IntValue(1)
        elif len(args) == 1:
            return args
        else:
            has_float = False
            ret = 1
            for arg in args:
                if (not isinstance(arg, IntValue)) and\
                   (not isinstance(arg, FloatValue)):
                    fatal('Mult', 'argument for + must be integer or float')
                if isinstance(arg, FloatValue):
                    has_float = True
                ret *= arg.value
            if has_float:
                return FloatValue(ret)
            else:
                return IntValue(ret)


class Div(PrimitiveFun):
    def __init__(self):
        super(Div, self).__init__('/', 1, sys.maxint)

    def apply(self, args):
        if len(args) == 1:
            return args

        has_float = False
        ret = 0
        for i, arg in enumerate(args):
            if (not isinstance(arg, IntValue)) and\
               (not isinstance(arg, FloatValue)):
                fatal('Sub', 'argument for + must be integer or float')
            if isinstance(arg, FloatValue):
                has_float = True
            if i == 0:
                ret = arg.value
            else:
                ret /= arg.value
        if has_float:
            return FloatValue(ret)
        else:
            return IntValue(ret)

class Print(PrimitiveFun):
    def __init__(self):
        super(Print, self).__init__('print', 1, sys.maxint)

    def apply(self, args):
        output = ''.join(map(str, args))
        print output

    def __str__(self):
        return '<Primitive Function: print>'

class And(PrimitiveFun):
    def __init__(self):
        super(And, self).__init__('and', 0, sys.maxint)

    def apply(self, args):
        ret = True
        for arg in args:
            if not isinstance(arg, BoolValue):
                fatal('And', 'argument for And must be boolean')
            ret = (ret and arg.value)
        return BoolValue(ret)

class Or(PrimitiveFun):
    def __init__(self):
        super(Or, self).__init__('or', 0, sys.maxint)

    def apply(self, args):
        ret = False
        for arg in args:
            if not isinstance(arg, BoolValue):
                fatal('And', 'argument for And must be boolean')
            ret = (ret or arg.value)
        return BoolValue(ret)

class Not(PrimitiveFun):
    def __init__(self):
        super(Not, self).__init__('not', 1, 1)

    def apply(self, args):
        arg = args[0]
        if not isinstance(arg, BoolValue):
            fatal('Not.apply', 'argument for Not must be boolean')
        ret = (not arg.value)
        return BoolValue(ret)


class Lt(PrimitiveFun):
    def __init__(self):
        super(Lt, self).__init__('<', 2, sys.maxint)

    def apply(self, args):
        for arg in args:
            if (not isinstance(arg, IntValue)) and\
               (not isinstance(arg, FloatValue)):
                fatal('Lt.apply', 'argument is not integer or float')
        ret = True
        for n1 in range(0, len(args)-1):
            arg1 = args[n1]
            arg2 = args[n1 + 1]

            if arg1.value < arg2.value:
                ret = True
            else:
                ret = False
        return BoolValue(ret)


class Lte(PrimitiveFun):
    def __init__(self):
        super(Lte, self).__init__('<=', 2, sys.maxint)

    def apply(self, args):
        for arg in args:
            if (not isinstance(arg, IntValue)) and\
               (not isinstance(arg, FloatValue)):
                fatal('Lt.apply', 'argument is not integer or float')
        ret = True
        for n1 in range(0, len(args)-1):
            arg1 = args[n1]
            arg2 = args[n1 + 1]

            if arg1.value <= arg2.value:
                ret = True
            else:
                ret = False
        return BoolValue(ret)


class Gt(PrimitiveFun):
    def __init__(self):
        super(Gt, self).__init__('>', 2, sys.maxint)

    def apply(self, args):
        for arg in args:
            if (not isinstance(arg, IntValue)) and\
               (not isinstance(arg, FloatValue)):
                fatal('Lt.apply', 'argument is not integer or float')
        ret = True
        for n1 in range(0, len(args)-1):
            arg1 = args[n1]
            arg2 = args[n1 + 1]

            if arg1.value > arg2.value:
                ret = True
            else:
                ret = False
        return BoolValue(ret)


class Gte(PrimitiveFun):
    def __init__(self):
        super(Gte, self).__init__('>=', 2, sys.maxint)

    def apply(self, args):
        for arg in args:
            if (not isinstance(arg, IntValue)) and\
               (not isinstance(arg, FloatValue)):
                fatal('Gte.apply', 'argument is not integer or float')
        ret = True
        for n1 in range(0, len(args)-1):
            arg1 = args[n1]
            arg2 = args[n1 + 1]

            if arg1.value < arg2.value:
                ret = True
            else:
                ret = False
        return BoolValue(ret)


class Eq(PrimitiveFun):
    def __init__(self):
        super(Eq, self).__init__('=', 2, sys.maxint)

    def apply(self, args):
        for arg in args:
            if (not isinstance(arg, IntValue)) and\
               (not isinstance(arg, FloatValue)):
                fatal('Lt.apply', 'argument is not integer or float')
        ret = True
        for n1 in range(0, len(args)-1):
            arg1 = args[n1]
            arg2 = args[n1 + 1]

            if arg1.value == arg2.value:
                ret = True
            else:
                ret = False
        return BoolValue(ret)

############## end primitive functions ######################

############## types ########################################
class Type(Value):
    def __init__(self, name):
        self.name = name

    def __str__(self):
        return self.name

    @staticmethod
    def subtype(ty1, ty2):
        pass

class BoolType(Type):
    def __init__(self):
        super(BoolType, self).__init__('Bool')

class IntType(Type):
    def __init__(self):
        super(IntType, self).__init__('Int')

class StrType(Type):
    def __init__(self):
        super(StrType, self).__init__('String')

class BasicType(object):
    BOOL = BoolType()
    INT = IntType()
    STR = StrType()

class AnyType(Type):
    def __init__(self):
        super(AnyType, self).__init__("Any")

class UnionType(Type):
    def __init__(self, *types):
        super(UnionType, self).__init__("U:")
        self.types = types
