#!/usr/bin/env python
#-*- coding:utf-8 -*-

"""
util functions
"""
import sys
import os.path

DEBUG = True

def read_file(name):
    name = os.path.expanduser(name)
    try:
        with open(name, 'rb') as fp:
            return fp.read().decode("utf8")
    except IOError:
        fatal('read_file', 'Can not open file', name)

def fatal(who, *msg):
    output = who + ": " + ' '.join(map(str, msg))
    print output
    sys.exit(-1)

def debug(*msg):
    if not DEBUG:
        return

    print ' '.join(map(str, msg))
    return False
# test
# print read_file("~/tmp/aa.py")

def even(n):
    pass

def odd(n):
    pass
