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

    def interp(self, e):
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

    def interp(self, e):
        return IntValue(self.value)

    def typecheck(self, tenv):
        return BasicType.INT

    def __str__(self):
        return str(self.value) + self.node_type('int')

class StrNode(Node):
    def __init__(self, lexeme, fname, start, end, line, col):
        super(StrNode, self).__init__(fname, start, end, line, col)
        self.value = lexeme.lstrip(STRING_BEGIN).rstrip(STRING_END)

    def interp(self, e):
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

    def interp(self, e):
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

    def interp(self, e):
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

    def interp(self, e):
        ret = []
        for ele in self.elements:
            ret.append(ele.interp(e))
        return VectorValue(ret)

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

    def interp(self, e):
        vec = self.value.interp(e)
        idx = self.index.interp(e)

        if not isinstance(vec, VectorValue):
            raise InterpError(patt.value, 'Not a vector value')
        if not isinstance(idx, IntValue):
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

    def interp(self, e):
        ret = {}
        for k in self.s_kv_map:
            ret[k] = self.s_kv_map[k].interp(e)
        return RecordLiteralValue(ret)

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

    def interp(self, e):
        rec = self.value.interp(e)
        if not isinstance(rec, RecordLiteralValue):
            raise InterpError(self, "Not a record literal value")
        if not isinstance(self.attr, NameNode):
            raise InterpError(self.attr, "Not a attribute name")
        attr = self.attr.id
        return rec.kv_map[attr]

    def __str__(self):
        return str(self.value) + RECORD_ATTR + str(self.attr)


class NameNode(Node):
    def __init__(self, lexeme, fname, start, end, line, col):
        super(NameNode, self).__init__(fname, start, end, line, col)
        self.id = lexeme

    def interp(self, e):
        ret = e.lookup(self.id)
        if not ret:
            raise InterpError(self, '%s is not binded in env' % self.id)
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

    def interp(self, e):
        test = self.test.interp(e)
        if not isinstance(test, BoolValue):
            raise InterpError(self.test, 'Test must be a boolean value')
        if test.value:
            return self.conseq.interp(e)
        else:
            return self.alt.interp(e)

    def __str__(self):
        ss = ' '.join([IF_KW, str(self.test), str(self.conseq), str(self.alt)])
        output = PAREN_BEGIN + self.node_type('if ') + ss + PAREN_END
        return output

class DefNode(Node):
    def __init__(self, pattern, val, fname, start, end, line, col):
        super(DefNode, self).__init__(fname, start, end, line, col)
        self.pattern = pattern
        self.value = val

    def interp(self, e):
        patt = self.pattern
        val = self.value.interp(e)
        bind(patt, val, e)

    def __str__(self):
        output = PAREN_BEGIN + self.node_type('def ') + DEFINE_KW + ' ' +\
                 str(self.pattern) + ' ' + str(self.value) + PAREN_END
        return output

class AssignNode(Node):
    def __init__(self, pattern, val, fname, start, end, line, col):
        super(AssignNode, self).__init__(fname, start, end, line, col)
        self.pattern = pattern
        self.value = val

    def interp(self, e):
        patt = self.pattern
        val = self.value.interp(e)
        assign(patt, val, e)

    def __str__(self):
        output = PAREN_BEGIN + self.node_type('ass ') + ASSIGN_KW +\
                 ' ' + str(self.pattern) + ' ' + str(self.value) + PAREN_END
        return output


class FunNode(Node):
    def __init__(self, args, body, fname, start, end, line, col):
        super(FunNode, self).__init__(fname, start, end, line, col)
        self.args = args
        self.body = body

    def interp(self, env):
        return Closure(self.args, self.body, env)

    def __str__(self):
        args_ss = PAREN_BEGIN + ' '.join(map(str, self.args)) + PAREN_END
        output = PAREN_BEGIN + self.node_type('fun ') + FUN_KW + ' ' +\
                 args_ss + ' ' + str(self.body) + PAREN_END
        return output


class ArgumentNode(Node):
    """
    Arguments for CallNode, support keyword argument and positional argument
    """
    def __init__(self, nodes, fname, start, end, line, col):
        self.nodes = nodes

        self.fname = fname
        self.start = start
        self.end = end
        self.line = line
        self.col = col

        self.positional = []
        self.keywords = {}

        # get separate index of positional arguments and keyword arguments
        sep_idx = len(nodes)
        for i in range(len(nodes)):
            if isinstance(nodes[i], KeywordNode):
                sep_idx = i
                break

        positional_nodes = nodes[0:sep_idx]
        keywords_nodes = nodes[sep_idx:]
        self.positional.extend(positional_nodes)

        keys = keywords_nodes[0::2]
        vals = keywords_nodes[1::2]
        for k in keys:
            if not isinstance(k, KeywordNode):
                raise ParserError(k, "must be a keyword node")
        for v in vals:
            if isinstance(v, KeywordNode):
                raise ParserError(v, "can't be a keyword node")

        if len(keys) != len(vals):
            raise ParserError(self, "the keys and values of keyword arguments must be same length")

        for k, v in zip(keys, vals):
            self.keywords[k] = v     # the key is KeywordNode instance

    def interp(self, env):
        positional = map(lambda arg: arg.interp(env), self.positional)
        keywords = {}
        for k in self.keywords:
            keywords[k.as_name()] = self.keywords[k].interp(env)
        return positional, keywords

    def __str__(self):
        ss = ' '.join(map(str, self.nodes))
        return PAREN_BEGIN + self.node_type('arg ') + ss + PAREN_END


class CallNode(Node):
    def __init__(self, fun, args, fname, start, end, line, col):
        super(CallNode, self).__init__(fname, start, end, line, col)
        self.fun = fun
        self.args = args        # ArgumentNode

    def interp(self, env):
        fv = self.fun.interp(env)
        positional_args, keyword_args = self.args.interp(env)

        if isinstance(fv, Closure):
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

            new_env = Env(fv.env)
            for k, v in kw.items():
                bind(k, v, new_env)

            callstack.append(self)
            ret = body.interp(new_env)
            callstack.pop()
            return ret
        elif isinstance(fv, PrimitiveFun):
            if not fv.check_arity(len(positional_args)):
                if fv.min_arity == fv.max_arity:
                    expected = str(fv.min_arity)
                else:
                    expected = "at least %s" % fv.min_arity
                msg = """the expected number of arguments doesn't match the given number
                expected: %s
                given %s""" % (expected, len(positional_args))
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

    def interp(self, e):
        e = Env(e)              # create new environment
        for s in self.statements[:-1]:
            s.interp(e)
        last = self.statements[len(self.statements)-1]
        return last.interp(e)

    def __str__(self):
        stats_str = '\n'.join(map(str, self.statements))
        output = PAREN_BEGIN + SEQ_KW + ' ' + stats_str + PAREN_END
        return output


def bind(patt, val, env):
    if isinstance(patt, NameNode):
        if env.lookup_local(patt.id):
            raise InterpError(patt, "Trying to redefine the name " + str(patt))
        env.put(patt.id, val)
    elif isinstance(patt, VectorNode) and isinstance(val, VectorValue):
        elements = patt.elements
        values = val.values
        if len(elements) != len(values):
            raise InterpError(patt, "the two vectors must have same length")
        for a, b in zip(patt.elements, val.values):
            bind(a, b, env)
    elif isinstance(patt, RecordLiteralNode) and\
         isinstance(val, RecordLiteralValue):
        p_map = patt.s_kv_map
        v_map = val.kv_map
        if len(p_map) != len(v_map):
            raise InterpError(patt, "the two record literal must have same length")
        if p_map.keys() != v_map.keys():
            raise InterpError(patt, "the two record literal must have same key set")
        for p_key in p_map:
            p_val = p_map[p_key]
            v_val = v_map[p_key]
            bind(p_val, v_val, env)
    else:
        raise InterpError(patt, "unkown pattern")


def assign(patt, val, env):
    if isinstance(patt, NameNode):
        env.set(patt.id, val)
    elif isinstance(patt, VectorNode) and isinstance(val, VectorValue):
        elements = patt.elements
        values = val.values
        if len(elements) != len(values):
            raise InterpError(patt, "the two vectors must have same length")
        for a, b in zip(patt.elements, val.values):
            assign(a, b, env)
    elif isinstance(patt, RecordLiteralNode) and\
         isinstance(val, RecordLiteralValue):
        p_map = patt.s_kv_map
        v_map = val.kv_map
        if len(p_map) != len(v_map):
            raise InterpError(patt, 'the two record literal must have same length')
        if p_map.keys() != v_map.keys():
            raise InterpError(patt, 'the two record literal must have same key set')
        for p_key in p_map:
            p_val = p_map[p_key]
            v_val = v_map[p_key]
            assign(p_val, v_val, env)
    elif isinstance(patt, SubscriptNode):
        vec = patt.value.interp(env)
        idx = patt.index.interp(env)
        if not isinstance(vec, VectorValue):
            raise InterpError(patt.value, 'Not a vector value')
        if not isinstance(idx, IntValue):
            raise InterpError(patt.index, 'index is not a Integer')
        if idx.value >= len(vec.values):
            raise InterpError(patt.index, 'out of index')
        vec.values[idx.value] = val

    elif isinstance(patt, AttrNode):
        rec = patt.value.interp(env)
        if not isinstance(rec, RecordLiteralValue):
            raise InterpError(patt.value, 'Not a record literal value')
        if not isinstance(patt.attr, NameNode):
            raise InterpError(patt.attr, 'Not a attribute name')
        attr = patt.attr.id
        if attr not in rec.kv_map:
            raise InterpError(patt, "record don't contain the attribute name")
        rec.kv_map[attr] = val
    else:
        raise InterpError(patt, "unkown pattern")
