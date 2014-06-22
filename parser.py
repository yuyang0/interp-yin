#!/usr/bin/env python
#-*- coding:utf-8 -*-

"""
parser
"""
from lexer import (Lexer, Token, DelimeterToken,
                   NumToken, StrToken, NameToken)
from constants import *
from ast import *
from util import *
from error import ParserError, LexicalError


class Parser(object):
    def __init__(self, fname):
        self.lex = Lexer(fname)

    def parse_pair(self, p):
        open_delim = p.open_delim
        close_delim = p.close_delim
        fname = open_delim.fname
        start = open_delim.start
        end = close_delim.end
        line = open_delim.line
        col = open_delim.col

        if open_delim.lexeme == PAREN_BEGIN:
            if len(p.elements) == 0:
                raise ParserError(open_delim, 'Pair should not be empty.')

            kw_tok = p.elements[0]

            if isinstance(kw_tok, NameToken):
                kw = p.elements[0].lexeme
                if kw == SEQ_KW:
                    statements = []
                    for i in p.elements[1:]:
                        statements.append(self.parse_tok_or_pair(i))
                    return BlockNode(statements, fname, start, end, line, col)

                elif kw == ASSIGN_KW:
                    if len(p.elements) != 3:
                        raise ParserError(open_delim, 'Assgin must have 3 elements')
                    pattern = self.parse_tok_or_pair(p.elements[1])
                    check_dup(pattern)
                    val = self.parse_tok_or_pair(p.elements[2])
                    return AssignNode(pattern, val, fname, start, end, line, col)
                elif kw == DEFINE_KW:
                    if len(p.elements) != 3:
                        raise ParserError(open_delim, 'Define must have 3 elements')
                    pattern = self.parse_tok_or_pair(p.elements[1])
                    check_dup(pattern)
                    val = self.parse_tok_or_pair(p.elements[2])
                    return DefNode(pattern, val, fname, start, end, line, col)
                elif kw == IF_KW:
                    if len(p.elements) != 4:
                        raise ParserError(open_delim, 'IF must have 4 elements')
                    test = self.parse_tok_or_pair(p.elements[1])
                    conseq = self.parse_tok_or_pair(p.elements[2])
                    alt = self.parse_tok_or_pair(p.elements[3])
                    return IfNode(test, conseq, alt, fname, start,
                              end, line, col)
                elif kw == FUN_KW:
                    if len(p.elements) < 2:
                        raise ParserError(open_delim, 'Fun must have 2 elements at least')
                    args_pair = p.elements[1]
                    if not isinstance(args_pair, Pair):
                        raise ParserError(open_delim, 'Formal Parameters should be a list')
                    args = self.parse_lst(args_pair.elements)
                    statements = self.parse_lst(p.elements[2:])
                    body = BlockNode(statements, fname, start, end, line, col)
                    return FunNode(args, body, fname, start, end, line, col)
            # application(Call)
            fun = self.parse_tok_or_pair(p.elements[0])
            parsed_args = self.parse_lst(p.elements[1:])
            if len(parsed_args) == 0:
                loc = close_delim
            else:
                loc = p.elements[1]
            args = ArgumentNode(parsed_args, loc.fname, loc.start,
                                end, loc.line, loc.col)
            return CallNode(fun, args, fname, start, end, line, col)
        # vector literal
        elif open_delim.lexeme == VECTOR_BEGIN:
            eles = self.parse_lst(p.elements)
            return VectorNode(eles, fname, start, end, line, col)
        # record literal
        elif open_delim.lexeme == RECORD_BEGIN:
            elements = self.parse_lst(p.elements)
            even_eles = elements[0::2]
            odd_eles = elements[1::2]
            if len(even_eles) != len(odd_eles):
                raise ParserError(open_delim, 'record literal must have even number of elements')
            keys = []
            for k in even_eles:
                if not isinstance(k, KeywordNode):
                    raise ParserError(k, 'Not a keyword')
                keys.append(k)
            kv_map = dict(zip(keys, odd_eles))
            return RecordLiteralNode(kv_map, fname, start, end, line, col)
        else:
            raise ParserError(open_delim, 'unkown pair')

    def parse_tok(self, tok):
        lexeme = tok.lexeme
        fname = tok.fname
        start = tok.start
        end = tok.end
        line = tok.line
        col = tok.col

        if isinstance(tok, NumToken):
            if '.' in lexeme:
                return FloatNode(lexeme, fname, start, end, line, col)
            else:
                return IntNode(lexeme, fname, start, end, line, col)
        elif isinstance(tok, StrToken):
            return StrNode(lexeme, fname, start, end, line, col)
        elif isinstance(tok, NameToken):
            # vector subscript
            if VECTOR_SUB in lexeme:
                val, idx = lexeme.split(VECTOR_SUB, 1)
                val = NameNode(val, fname, start, end, line, col)
                idx = IntNode(idx, fname, start, end, line, col)
                return SubscriptNode(val, idx, fname, start, end, line, col)
            # record attribute access
            if RECORD_ATTR in lexeme:
                val, attr = lexeme.split(RECORD_ATTR, 1)
                val = NameNode(val, fname, start, end, line, col)
                attr = NameNode(attr, fname, start, end, line, col)
                return AttrNode(val, attr, fname, start, end, line, col)
            # boolean
            if lexeme in (TRUE_KW, FALSE_KW):
                return BoolNode(lexeme, fname, start, end, line, col)
            # keyword
            if lexeme.startswith(KEYWORD_PREFIX):
                return KeywordNode(lexeme, fname, start, end, line, col)
            else:
                return NameNode(lexeme, fname, start, end, line, col)

    def parse_tok_or_pair(self, pt):
        if isinstance(pt, Token):
            return self.parse_tok(pt)
        elif isinstance(pt, Pair):
            return self.parse_pair(pt)

    def parse_lst(self, lst):
        ret = []
        for i in lst:
            ret.append(self.parse_tok_or_pair(i))
        return ret

    def parse(self):
        first = self.next_pair_or_tok(0)
        pt = first
        statements = []
        while pt:
            statements.append(self.parse_tok_or_pair(pt))
            pt = self.next_pair_or_tok(0)
        last = statements[len(statements)-1]
        return BlockNode(statements, first.fname, first.start, last.end,
                         first.line, first.col)

    def next_pair_or_tok(self, deepth):
        try:
            tok = self.lex.next_token()
        except LexicalError, e:
            fatal(str(e))

        if not tok:
            return False

        if is_open(tok.lexeme):
            open_delim = tok
            elements = []
            while True:
                pt = self.next_pair_or_tok(deepth+1)
                if not pt:
                    raise ParserError(tok, "unbalanced delimeter")
                if isinstance(pt, DelimeterToken) and\
                   match_delimeter(open_delim.lexeme, pt.lexeme):
                    break
                elements.append(pt)
            close_delim = pt
            return Pair(open_delim, close_delim, elements)
        elif is_close(tok.lexeme) and deepth == 0:
            raise ParserError(tok, "unbalanced delimeter")
        else:
            return tok

class Pair(object):
    '''
    content between (), [], {}
    '''
    def __init__(self, first, last, elements):
        self.elements = elements
        self.open_delim = first
        self.close_delim = last

        self.fname = first.fname
        self.start = first.start
        self.end = last.end
        self.line = first.line
        self.col = first.col

    def __str__(self):
        output = str(self.open_delim) + ' '.join(map(str, self.elements)) +\
                 str(self.close_delim)
        return output


def check_dup(patt):
    if isinstance(patt, RecordLiteralNode):
        ret = set()
        for k in patt.kv_map:
            v = patt.kv_map[k]
            if v in ret and isinstance(v, NameNode):
                raise ParserError(v, "duplicate variable")
            else:
                ret.add(v)

    elif isinstance(patt, VectorNode):
        ret = set()
        for e in patt.elements:
            if e in ret and isinstance(e, NameNode):
                raise ParserError(e, "duplicate variable")
            else:
                ret.add(e)
    else:
        return True


if __name__ == '__main__':
    import sys
    p = Parser(sys.argv[1])
    try:
        node = p.parse()
    except ParserError, e:
        fatal(str(e))
    print node
