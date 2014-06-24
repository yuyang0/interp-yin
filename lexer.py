#!/usr/bin/env python
#-*- coding:utf-8 -*-

"""
Lexer of Lisp
"""
import re
import sys

from util import *
from constants import *
from error import LexicalError

reload(sys)
sys.setdefaultencoding("utf8")

# Number regexp(Hexadecimal, Decimal, Octal, Binary, float)
NUM_REGEX = re.compile(r'([+-]?)(0x[\dA-F]+|[1-9]\d*|0[0-7]*|0b[01]+|\d+\.\d+)[\s\(\)\[\]\{\}]', re.I)
# String Regexp
STR_REGEX = re.compile(r'"([^\n]*)"')
################## global functions ##########

def is_name_char(char):
    return char.isalnum() or char in '~!@#$%^&*-_=+:;<>,=?/.'
############## end global #####################


class Token(object):
    def __init__(self, ty, lexeme, fname, start, end, line, col):
        self.ty = ty            # Token type, Number, String, Name etc
        self.lexeme = lexeme

        self.fname = fname
        self.start = start
        self.end = end
        self.line = line
        self.col = col

    def __str__(self):
        output = "%-12s: %s" % (self.ty, self.lexeme)
        return output


class DelimeterToken(Token):
    def __init__(self, lexeme, fname, start, end, line, col):
        super(DelimeterToken, self).__init__("Delimeter", lexeme,
                                             fname, start, end, line, col)


class NumToken(Token):
    def __init__(self, lexeme, fname, start, end, line, col):
        super(NumToken, self).__init__("Number", lexeme,
                                       fname, start, end, line, col)


class StrToken(Token):
    def __init__(self, lexeme, fname, start, end, line, col):
        super(StrToken, self).__init__("String", lexeme,
                                       fname, start, end, line, col)


class NameToken(Token):
    def __init__(self, lexeme, fname, start, end, line, col):
        super(NameToken, self).__init__("Name", lexeme,
                                        fname, start, end, line, col)


class Lexer(object):
    def __init__(self, fname, text=None):
        if text:
            self.text = text
        else:
            self.text = read_file(fname)
        # append a space to the end of the source code string to avoid
        # some trick problems
        self.text += " "

        self.fname = fname
        self.offset = 0
        self.line = 1
        self.col = 0

        self.peek = self.text[0]

    def text_startswith(self, prefix):
        return self.text.startswith(prefix, self.offset)

    def forward(self, n=1):
        for i in range(n):
            char = self.text[self.offset]
            if char == '\n':
                self.line += 1
                self.col = 0
                self.offset += 1
            else:
                self.col += 1
                self.offset += 1

    def at_end(self):
        return self.offset >= len(self.text)

    def not_at_end(self):
        return self.offset < len(self.text)

    def skip_spaces(self):
        if self.at_end():
            return False

        char = self.text[self.offset]
        if char.isspace():
            while self.not_at_end() and char.isspace():
                self.forward()
                if self.not_at_end():
                    char = self.text[self.offset]
                else:
                    break
            return True
        else:
            return False

    def skip_comments(self):
        if self.at_end():
            return False

        if self.text_startswith(COMMENT_PREFIX):
            line_end = self.text.find('\n', self.offset)
            if line_end == -1:
                line_end = len(self.text) - 1
            self.forward(line_end - self.offset + 1)
            return True
        else:
            return False

    def skip_spaces_comments(self):
        while self.skip_spaces() or self.skip_comments():
            pass

    def scan_string(self):
        if self.at_end():
            return False

        start = self.offset
        end = self.text.find(STRING_END, start+len(STRING_BEGIN))
        if end == -1:
            raise LexicalError(self.fname, self.line, self.col,
                               "no string end quote mark found")
        else:
            end += len(STRING_END)

        lexeme = self.text[start:end]
        if '\n' in lexeme:
            raise LexicalError(self.fname, self.line, self.col,
                               "string in many line")

        tok = StrToken(lexeme, self.fname, start, end,
                       self.line, self.col)
        self.forward(len(lexeme))
        return tok

    def scan_name(self):
        if self.at_end():
            return False

        char = self.text[self.offset]
        start = self.offset
        start_line = self.line
        start_col = self.col
        while is_name_char(char):
            self.forward()
            if self.not_at_end():
                char = self.text[self.offset]
            else:
                break
        end = self.offset
        lexeme = self.text[start:end]
        tok = NameToken(lexeme, self.fname, start, end,
                        start_line, start_col)
        return tok

    def next_token(self):
        self.skip_spaces_comments()
        if self.at_end():
            return False

        first_char = self.text[self.offset]
        if is_delimeter(first_char):
            tok = DelimeterToken(first_char, self.fname, self.offset,
                                 self.offset+1, self.line, self.col)
            self.forward()
            return tok
        # string
        if self.text_startswith(STRING_BEGIN):
            return self.scan_string()
        # number
        m = NUM_REGEX.match(self.text, self.offset)
        if m:
            lexeme = ''.join(m.groups())
            tok = NumToken(lexeme, self.fname, self.offset,
                           self.offset + len(lexeme), self.line, self.col)
            self.forward(len(lexeme))
            return tok

        # Name
        if is_name_char(first_char):
            return self.scan_name()
        else:
            raise LexicalError(self.fname, self.line, self.col,
                               "unkown token: %s" % first_char)


if __name__ == '__main__':
    import sys
    import readline
    if len(sys.argv) == 1:
        ss = raw_input("==> ")
        lex = Lexer("stdin", ss)
    else:
        lex = Lexer(sys.argv[1])
    tok = lex.next_token()
    while tok:
        print tok
        tok = lex.next_token()
