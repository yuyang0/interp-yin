#!/usr/bin/env python
#-*- coding:utf-8 -*-

"""
ast of lisp
"""

from constants import *
from values import *
from util import *
from environment import *
from error import InterpError, ParserError

class Node(object):
    def __init__(self, fname, start, end, line, col):
        self.fname = fname
        self.start = start
        self.end = end
        self.line = line
        self.col = col

    def node_type(self, ty):
        AA = True
        if AA:
            return '@' + str(ty)
        else:
            return ''

class FloatNode(Node):
    def __init__(self, lexeme, fname, start, end, line, col):
        super(FloatNode, self).__init__(fname, start, end, line, col)
        try:
            self.value = float(lexeme)          # need fixed
        except ValueError:
            raise ParserError(self, "invlid literal for float")

    def interp(self, tbl):
        return FloatValue(self.value)

    def __str__(self):
        return str(self.value) + self.node_type('float')

class IntNode(Node):
    def __init__(self, lexeme, fname, start, end, line, col):
        super(IntNode, self).__init__(fname, start, end, line, col)
        self.value = self.parse_number(lexeme)

    def parse_number(self, lexeme):
        # skip the sign
        lexeme = lexeme.lstrip('+-').lower()

        if lexeme.startswith('0x'):
            base = 16
        elif lexeme.startswith('0b'):
            base = 2
        elif lexeme.startswith('0'):
            base = 8
        else:
            base = 10
        try:
            return int(lexeme, base)
        except ValueError:
            raise ParserError(self, "Not a number")

    def interp(self, tbl):
        return IntValue(self.value)

    def typecheck(self, tenv):
        return BasicType.INT

    def __str__(self):
        return str(self.value) + self.node_type('int')

class StrNode(Node):
    def __init__(self, lexeme, fname, start, end, line, col):
        super(StrNode, self).__init__(fname, start, end, line, col)
        self.value = lexeme.lstrip(STRING_BEGIN).rstrip(STRING_END)

    def interp(self, tbl):
        return StrValue(self.value)

    def typecheck(self, tenv):
        return BasicType.STR

    def __str__(self):
        return STRING_BEGIN + self.value + STRING_END + self.node_type('str')

class BoolNode(Node):
    def __init__(self, lexeme, fname, start, end, line, col):
        super(BoolNode, self).__init__(fname, start, end, line, col)
        if lexeme == TRUE_KW:
            self.value = True
        else:
            self.value = False

    def interp(self, tbl):
        return BoolValue(self.value)

    def typecheck(self, tenv):
        return BasicType.BOOL

    def __str__(self):
        return (TRUE_KW if self.value else FALSE_KW) + self.node_type('bool')

class KeywordNode(Node):
    def __init__(self, lexeme, fname, start, end, line, col):
        super(KeywordNode, self).__init__(fname, start, end, line, col)
        self.id = lexeme[len(KEYWORD_PREFIX):]

    def as_name(self):
        return NameNode(self.id, self.fname, self.start+len(KEYWORD_PREFIX),
                        self.end, self.line, self.col)

    def interp(self, tbl):
        raise InterpError(self, "keyword can't be evaluated as value")

    def __str__(self):
        return KEYWORD_PREFIX + self.id + self.node_type('kw')

    def __eq__(self, other):
        return self.id == other.id

    def __hash__(self):
        return hash(self.id)


class VectorNode(Node):
    def __init__(self, elements, fname, start, end, line, col):
        super(VectorNode, self).__init__(fname, start, end, line, col)
        self.elements = elements

    def interp(self, tbl):
        ret = map(lambda ele: ele.interp(tbl), self.elements)
        return VectorValue(ret)

    def check_dup(self):
        ret = set()
        for e in self.elements:
            if e in ret and IS(e, NameNode):
                raise ParserError(e, "duplicate variable")
            else:
                ret.add(e)

    def __str__(self):
        ss = ' '.join(map(str, self.elements))
        output = VECTOR_BEGIN + self.node_type('vec ') + ss + VECTOR_END
        return output


class SubscriptNode(Node):
    """
    Vector Subscript Node
    """
    def __init__(self, val, idx, fname, start, end, line, col):
        super(SubscriptNode, self).__init__(fname, start, end, line, col)
        self.value = val
        self.index = idx

    def interp(self, tbl):
        vec = self.value.interp(tbl)
        idx = self.index.interp(tbl)

        if not IS(vec, VectorValue):
            raise InterpError(patt.value, 'Not a vector value')
        if not IS(idx, IntValue):
            raise InterpError(patt.index, 'index is not a Integer')
        if idx.value >= len(vec.values):
            raise InterpError(patt.index, 'out of index')

        return vec.values[idx.value]

    def __str__(self):
        return str(self.value) + VECTOR_SUB + str(self.index)


class RecordLiteralNode(Node):
    def __init__(self, kv_map, fname, start, end, line, col):
        super(RecordLiteralNode, self).__init__(fname, start, end, line, col)
        self.kv_map = kv_map    # {KeywordNode => Node}
        self.s_kv_map = {}      # {KeywordNode.id => Node}
        for k in kv_map:
            self.s_kv_map[k.id] = kv_map[k]

    def interp(self, tbl):
        ret = {}
        for k in self.s_kv_map:
            ret[k] = self.s_kv_map[k].interp(tbl)
        return RecordLiteralValue(ret)

    def check_dup(self):
        ret = set()
        for v in self.kv_map.values():
            if v in ret and IS(v, NameNode):
                raise ParserError(v, "duplicate variable")
            else:
                ret.add(v)

    def __str__(self):
        ss = ' '.join(map(lambda k: str(k)+' '+str(self.kv_map[k]), self.kv_map))
        output = RECORD_BEGIN + self.node_type('rec ') + ss + RECORD_END
        return output


class RecordDefNode(Node):
    def __init__(self):
        pass

    def __str__(self):
        pass


class AttrNode(Node):
    """
    Record Attribute Node
    """
    def __init__(self, val, attr, fname, start, end, line, col):
        super(AttrNode, self).__init__(fname, start, end, line, col)
        self.value = val
        self.attr = attr

    def interp(self, tbl):
        rec = self.value.interp(tbl)
        if not IS(rec, RecordLiteralValue):
            raise InterpError(self, "Not a record literal value")
        if not IS(self.attr, NameNode):
            raise InterpError(self.attr, "Not a attribute name")
        attr = self.attr.id
        return rec.kv_map[attr]

    def __str__(self):
        return str(self.value) + RECORD_ATTR + str(self.attr)


class NameNode(Node):
    def __init__(self, lexeme, fname, start, end, line, col):
        super(NameNode, self).__init__(fname, start, end, line, col)
        self.id = lexeme

    def interp(self, tbl):
        ret = tbl.lookup_value(self.id)
        if not ret:
            raise InterpError(self, 'unbound varibale: %s' % self.id)
        return ret

    def __str__(self):
        return self.id + self.node_type('name')

    def __eq__(self, other):
        return self.id == other.id

    def __hash__(self):
        return hash(self.id)


class IfNode(Node):
    def __init__(self, test, conseq, alt, fname, start, end, line, col):
        super(IfNode, self).__init__(fname, start, end, line, col)
        self.test = test
        self.conseq = conseq
        self.alt = alt

    def interp(self, tbl):
        test = self.test.interp(tbl)
        if not IS(test, BoolValue):
            raise InterpError(self.test, 'Test is not a boolean value')
        if test.value:
            return self.conseq.interp(tbl)
        else:
            return self.alt.interp(tbl)

    def __str__(self):
        ss = ' '.join([IF_KW, str(self.test), str(self.conseq), str(self.alt)])
        output = PAREN_BEGIN + self.node_type('if ') + ss + PAREN_END
        return output

class DefNode(Node):
    def __init__(self, pattern, val, fname, start, end, line, col):
        super(DefNode, self).__init__(fname, start, end, line, col)
        self.pattern = pattern
        self.value = val

    def interp(self, tbl):
        patt = self.pattern
        val = self.value.interp(tbl)
        bind(patt, val, tbl)

    def __str__(self):
        output = PAREN_BEGIN + self.node_type('def ') + DEFINE_KW + ' ' +\
                 str(self.pattern) + ' ' + str(self.value) + PAREN_END
        return output

class AssignNode(Node):
    def __init__(self, pattern, val, fname, start, end, line, col):
        super(AssignNode, self).__init__(fname, start, end, line, col)
        self.pattern = pattern
        self.value = val

    def interp(self, tbl):
        patt = self.pattern
        val = self.value.interp(tbl)
        assign(patt, val, tbl)

    def __str__(self):
        output = PAREN_BEGIN + self.node_type('ass ') + ASSIGN_KW +\
                 ' ' + str(self.pattern) + ' ' + str(self.value) + PAREN_END
        return output


class FunNode(Node):
    def __init__(self, args, properties, body, fname, start, end, line, col):
        super(FunNode, self).__init__(fname, start, end, line, col)
        self.args = args
        self.properties = properties
        self.body = body

    def interp(self, tbl):
        properties = self.properties
        if properties:
            self.interp_properties(tbl)
        return Closure(self.args, properties, self.body, tbl)

    def __str__(self):
        args_ss = PAREN_BEGIN + ' '.join(map(str, self.args)) + PAREN_END
        output = PAREN_BEGIN + self.node_type('fun ') + FUN_KW + ' ' +\
                 args_ss + ' ' + str(self.body) + PAREN_END +\
                 "<<" + str(self.properties) + ">>"
        return output

    def interp_properties(self, env):
        properties = self.properties
        tbl = SymTable()
        for name in properties.table:
            entry = properties.table[name]
            pros = {}
            for k, v in entry.items():
                if IS(v, Node):
                    pros[k] = v.interp(env)
                else:
                    pros[k] = v
            tbl.table[name] = pros
        return tbl



class ArgumentNode(Node):
    """
    Arguments for CallNode, support keyword argument and positional argument
    """
    def __init__(self, pos_nodes, kw_nodes, fname, start, end, line, col):
        self.positional = pos_nodes
        self.keywords = kw_nodes

        self.fname = fname
        self.start = start
        self.end = end
        self.line = line
        self.col = col

    def interp(self, tbl):
        positional = map(lambda arg: arg.interp(tbl), self.positional)
        keywords = {}
        for k in self.keywords:
            keywords[k.as_name()] = self.keywords[k].interp(tbl)
        return positional, keywords

    def __str__(self):
        ss = ' '.join(map(str, self.positional)) + ' ' + str(self.keywords)
        return PAREN_BEGIN + self.node_type('arg ') + ss + PAREN_END


class CallNode(Node):
    def __init__(self, fun, args, fname, start, end, line, col):
        super(CallNode, self).__init__(fname, start, end, line, col)
        self.fun = fun
        self.args = args        # ArgumentNode

    def interp(self, tbl):
        fv = self.fun.interp(tbl)
        positional_args, keyword_args = self.args.interp(tbl)

        if IS(fv, Closure):
            formal_args = fv.args
            body = fv.body
            if len(positional_args) + len(keyword_args) != len(formal_args):
                raise InterpError(self.args, "wrong number of actual arguments")
            kw = {}
            for i in range(len(positional_args)):
                param = formal_args[i]
                kw[param] = positional_args[i]
            for i in range(len(positional_args), len(formal_args)):
                param = formal_args[i]
                if param not in keyword_args:
                    raise InterpError(self.args, "param name(%s) is not a keyword"% param)
                kw[param] = keyword_args[param]

            new_tbl = SymTable(fv.tbl)
            for k, v in kw.items():
                bind(k, v, new_tbl)

            callstack.append(self)
            ret = body.interp(new_tbl)
            callstack.pop()
            return ret
        elif IS(fv, PrimitiveFun):
            if not fv.check_arity(len(positional_args)):
                if fv.min_arity == fv.max_arity:
                    expected = str(fv.min_arity)
                else:
                    expected = "at least %s" % fv.min_arity
                msg = """the expected %s arguments, but given %s
                """ % (expected, len(positional_args))
                raise InterpError(self,  msg)
            return fv.apply(positional_args)
        else:
            raise InterpError(self, "unkown type function")

    def __str__(self):
        output = PAREN_BEGIN + self.node_type('call ') + str(self.fun) + ' ' +\
                 str(self.args) + PAREN_END
        return output


class BlockNode(Node):
    def __init__(self, statements, fname, start, end, line, col):
        super(BlockNode, self).__init__(fname, start, end, line, col)
        self.statements = statements

    def interp(self, tbl):
        tbl = SymTable(tbl)              # create new symbol table
        for s in self.statements[:-1]:
            s.interp(tbl)
        last = self.statements[len(self.statements)-1]
        return last.interp(tbl)

    def __str__(self):
        stats_str = '\n'.join(map(str, self.statements))
        output = PAREN_BEGIN + SEQ_KW + ' ' + stats_str + PAREN_END
        return output


def bind(patt, val, tbl):
    if IS(patt, NameNode):
        if tbl.lookup_value_local(patt.id):
            raise InterpError(patt, "Trying to redefine the name " + str(patt))
        tbl.put_value(patt.id, val)
    elif IS(patt, VectorNode) and IS(val, VectorValue):
        elements = patt.elements
        values = val.values
        if len(elements) != len(values):
            raise InterpError(patt, "the two vectors must have same length")
        for a, b in zip(patt.elements, val.values):
            bind(a, b, tbl)
    elif IS(patt, RecordLiteralNode) and IS(val, RecordLiteralValue):
        p_map = patt.s_kv_map
        v_map = val.kv_map
        if len(p_map) != len(v_map):
            raise InterpError(patt, "the two record literal must have same length")
        if p_map.keys() != v_map.keys():
            raise InterpError(patt, "the two record literal must have same key set")
        for p_key in p_map:
            p_val = p_map[p_key]
            v_val = v_map[p_key]
            bind(p_val, v_val, tbl)
    else:
        raise InterpError(patt, "unkown pattern")


def assign(patt, val, tbl):
    if IS(patt, NameNode):
        tbl.set_value(patt.id, val)
    elif IS(patt, VectorNode) and IS(val, VectorValue):
        elements = patt.elements
        values = val.values
        if len(elements) != len(values):
            raise InterpError(patt, "the two vectors must have same length")
        for a, b in zip(patt.elements, val.values):
            assign(a, b, tbl)
    elif IS(patt, RecordLiteralNode) and IS(val, RecordLiteralValue):
        p_map = patt.s_kv_map
        v_map = val.kv_map
        if len(p_map) != len(v_map):
            raise InterpError(patt, 'the two record literal must have same length')
        if p_map.keys() != v_map.keys():
            raise InterpError(patt, 'the two record literal must have same key set')
        for p_key in p_map:
            p_val = p_map[p_key]
            v_val = v_map[p_key]
            assign(p_val, v_val, tbl)
    elif IS(patt, SubscriptNode):
        vec = patt.value.interp(tbl)
        idx = patt.index.interp(tbl)
        if not IS(vec, VectorValue):
            raise InterpError(patt.value, 'Not a vector value')
        if not IS(idx, IntValue):
            raise InterpError(patt.index, 'index is not a Integer')
        if idx.value >= len(vec.values):
            raise InterpError(patt.index, 'out of index')
        vec.values[idx.value] = val

    elif IS(patt, AttrNode):
        rec = patt.value.interp(tbl)
        if not IS(rec, RecordLiteralValue):
            raise InterpError(patt.value, 'Not a record literal value')
        if not IS(patt.attr, NameNode):
            raise InterpError(patt.attr, 'Not a attribute name')
        attr = patt.attr.id
        if attr not in rec.kv_map:
            raise InterpError(patt, "record don't contain the attribute name")
        rec.kv_map[attr] = val
    else:
        raise InterpError(patt, "unkown pattern")
