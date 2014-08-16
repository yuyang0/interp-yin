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
    def __init__(self, fname, text=None):
        self.lex = Lexer(fname, text)

    def parse_pair(self, p):
        open_delim = p.open_delim
        close_delim = p.close_delim
        fname = open_delim.fname
        start = open_delim.start
        end = close_delim.end
        line = open_delim.line
        col = open_delim.col

        if IS(p, ParenPair):
            if len(p.elements) == 0:
                raise ParserError(open_delim, 'Pair should not be empty.')

            kw_tok = p.elements[0]

            if isinstance(kw_tok, NameToken):
                kw = p.elements[0].lexeme
                # the template for error message
                msg_tpl = """
                 %s: bad syntax;
                expect %s parts after keyword, but given %s parts
                """
                if kw == SEQ_KW:
                    statements = []
                    for i in p.elements[1:]:
                        statements.append(self.parse_tok_or_pair(i))
                    return BlockNode(statements, fname, start, end, line, col)

                elif kw == ASSIGN_KW:
                    if len(p.elements) != 3:
                        err_msg = msg_tpl % (ASSIGN_KW, 2, len(p.elements)-1)
                        raise ParserError(open_delim, err_msg)
                    patt = self.parse_tok_or_pair(p.elements[1])
                    if IS(patt, VectorNode) or IS(patt, RecordLiteralNode):
                        patt.check_dup()
                    val = self.parse_tok_or_pair(p.elements[2])
                    return AssignNode(patt, val, fname, start, end, line, col)
                elif kw == DEFINE_KW:
                    if len(p.elements) != 3:
                        err_msg = msg_tpl % (DEFINE_KW, 2, len(p.elements)-1)
                        raise ParserError(open_delim, err_msg)
                    patt = self.parse_tok_or_pair(p.elements[1])
                    if IS(patt, VectorNode) or IS(patt, RecordLiteralNode):
                        patt.check_dup()
                    val = self.parse_tok_or_pair(p.elements[2])
                    return DefNode(patt, val, fname, start, end, line, col)
                elif kw == IF_KW:
                    if len(p.elements) != 4:
                        if len(p.elements) == 3:
                            msg = "if: missing an \"else\" expression"
                        else:
                            msg = """if: bad syntax;
                            has %d part after keyword""" % len(p.elements)-1
                        raise ParserError(open_delim, msg)
                    test = self.parse_tok_or_pair(p.elements[1])
                    conseq = self.parse_tok_or_pair(p.elements[2])
                    alt = self.parse_tok_or_pair(p.elements[3])
                    return IfNode(test, conseq, alt, fname, start,
                                  end, line, col)
                elif kw == FUN_KW:    # anonymous function
                    if len(p.elements) < 2:
                        err_msg = msg_tpl % (FUN_KW, "at least 1", len(p.elements)-1)
                        raise ParserError(open_delim, err_msg)
                    params_pair = p.elements[1]
                    if not isinstance(params_pair, Pair):
                        raise ParserError(open_delim, 'Formal Parameters should be a list')
                    param_names, properties = self.parse_properties(params_pair.elements)
                    # construct body
                    statements = self.parse_lst(p.elements[2:])
                    body = BlockNode(statements, fname, start, end, line, col)
                    return FunNode(param_names, properties, body,
                                   fname, start, end, line, col)
            # application(Call)
            fun = self.parse_tok_or_pair(p.elements[0])
            parsed_args = self.parse_lst(p.elements[1:])
            if len(parsed_args) == 0:
                loc = close_delim
            else:
                loc = p.elements[1]
            positional, keywords = Parser.parse_arguments(parsed_args)
            args = ArgumentNode(positional, keywords, loc.fname, loc.start,
                                end, loc.line, loc.col)
            return CallNode(fun, args, fname, start, end, line, col)
        # vector literal
        elif IS(p, SquarePair):
            eles = self.parse_lst(p.elements)
            return VectorNode(eles, fname, start, end, line, col)
        # record literal
        elif IS(p, CurlyPair):
            elements = self.parse_lst(p.elements)
            kv_map = dict(Parser.parse_map(elements))
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

    def parse_properties(self, lst):
        params = []
        properties = None
        for entry in lst:
            if isinstance(entry, NameToken):
                params.append(self.parse_tok(entry))
            if isinstance(entry, Pair):
                eles = entry.elements
                if len(eles) < 2:
                    raise ParserError(entry, "at least 2 elements")
                if not properties:
                    properties = SymTable()
                nodes = self.parse_lst(eles)
                name = nodes[0]
                ty = nodes[1]
                params.append(name)
                properties.put_type(name.id, ty)

                for k, v in Parser.parse_map(nodes[2:]):
                    properties.put(name.id, k.id, v)

        return params, properties

    @staticmethod
    def parse_map(nodes):
        keys = nodes[0::2]
        vals = nodes[1::2]
        for k in keys:
            if not isinstance(k, KeywordNode):
                raise ParserError(k, "must be a keyword node")
        for v in vals:
            if isinstance(v, KeywordNode):
                raise ParserError(v, "can't be a keyword node")
        if len(keys) != len(vals):
            raise ParserError(self, "the keys and values don't have same length")
        return zip(keys, vals)

    @staticmethod
    def parse_arguments(nodes):
        positional = []
        keywords = {}

        # get separate index of positional arguments and keyword arguments
        sep_idx = len(nodes)
        for i in range(len(nodes)):
            if isinstance(nodes[i], KeywordNode):
                sep_idx = i
                break

        positional_nodes = nodes[0:sep_idx]
        keywords_nodes = nodes[sep_idx:]
        positional.extend(positional_nodes)

        for k, v in Parser.parse_map(keywords_nodes):
            keywords[k] = v     # the key is KeywordNode instance
        return positional, keywords

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
            if open_delim.lexeme == PAREN_BEGIN:
                return ParenPair(open_delim, close_delim, elements)
            elif open_delim.lexeme == SQUARE_BEGIN:
                return SquarePair(open_delim, close_delim, elements)
            elif open_delim.lexeme == CURLY_BEGIN:
                return CurlyPair(open_delim, close_delim, elements)
            else:
                raise ParserError(open_delim, "unkown pair")
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

    # @staticmethod
    # def next_pair_or_tok(lex):
    #     return Pair.next_pair_or_tok_1(lex, 0)

    # @staticmethod
    # def next_pair_or_tok_1(lex, deepth):
    #     try:
    #         tok = lex.next_token()
    #     except LexicalError, e:
    #         fatal(str(e))

    #     if not tok:
    #         return False

    #     if is_open(tok.lexeme):
    #         open_delim = tok
    #         elements = []
    #         while True:
    #             pt = Pair.next_pair_or_tok_1(deepth+1)
    #             if not pt:
    #                 raise ParserError(tok, "unbalanced delimeter")
    #             if isinstance(pt, DelimeterToken) and\
    #                match_delimeter(open_delim.lexeme, pt.lexeme):
    #                 break
    #             elements.append(pt)
    #         close_delim = pt
    #         if open_delim.lexeme == PAREN_BEGIN:
    #             return ParenPair(open_delim, close_delim, elements)
    #         elif open_delim.lexeme == SQUARE_BEGIN:
    #             return SquarePair(open_delim, close_delim, elements)
    #         elif open_delim.lexeme == CURLY_BEGIN:
    #             return CurlyPair(open_delim, close_delim, elements)
    #         else:
    #             raise ParserError(open_delim, "unkown pair")
    #     elif is_close(tok.lexeme) and deepth == 0:
    #         raise ParserError(tok, "unbalanced delimeter")
    #     else:
    #         return tok


class ParenPair(Pair):
    def __init__(self, first, last, elements):
        super(ParenPair, self).__init__(first, last, elements)


class SquarePair(Pair):
    def __init__(self, first, last, elements):
        super(SquarePair, self).__init__(first, last, elements)


class CurlyPair(Pair):
    def __init__(self, first, last, elements):
        super(CurlyPair, self).__init__(first, last, elements)


if __name__ == '__main__':
    import sys
    import readline
    if len(sys.argv) == 1:
        ss = raw_input("==> ")
        p = Parser("stdin", ss)
    else:
        p = Parser(sys.argv[1])
    try:
        node = p.parse()
    except ParserError, e:
        fatal(str(e))
    print node
