#!/usr/bin/env python
#-*- coding:utf-8 -*-

"""
constants
"""
################# global constants ############
COMMENT_PREFIX = '--'
STRING_BEGIN = "\""
STRING_END = "\""
STRING_ESCAPE = "\\"

# KEYWORDS
IF_KW = 'if'
FUN_KW = 'fun'
DEFINE_KW = 'define'
ASSIGN_KW = 'set!'
SEQ_KW = 'seq'

TRUE_KW = 'true'
FALSE_KW = 'false'

# DELIMETER
PAREN_BEGIN = '('
PAREN_END = ')'
RECORD_BEGIN = '{'
RECORD_END = '}'
VECTOR_BEGIN = '['
VECTOR_END = ']'

SQUARE_BEGIN = '['
SQUARE_END = ']'
CURLY_BEGIN = '{'
CURLY_END = '}'
# ATTR_ACCESS = '.'
RECORD_ATTR = '.'
VECTOR_SUB = '#'
KEYWORD_PREFIX = ':'

QUOTE_PREFIX = "'"

callstack = []

def is_delimeter(ss):
    return ss == PAREN_BEGIN or\
        ss == PAREN_END or\
        ss == RECORD_BEGIN or\
        ss == RECORD_END or\
        ss == VECTOR_BEGIN or \
        ss == VECTOR_END

def is_open(ss):
    return ss == PAREN_BEGIN or\
        ss == VECTOR_BEGIN or\
        ss == RECORD_BEGIN

def is_close(ss):
    return ss == PAREN_END or\
        ss == VECTOR_END or\
        ss == RECORD_END

def match_delimeter(d1, d2):
    return (d1 == PAREN_BEGIN and d2 == PAREN_END) or\
        (d1 == VECTOR_BEGIN and d2 == VECTOR_END) or\
        (d1 == RECORD_BEGIN and d2 == RECORD_END)
