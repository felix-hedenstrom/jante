#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import math
import re

class token:
    def __init__(self, tpe, value, offset=0):
        self.tpe = tpe
        self.value = value
        self.offset = offset
    
    def __eq__(self, other):
        return self.tpe == other.tpe and self.value == other.value
    
    def __repr__(self):
        return "token({}, {})".format(repr(self.tpe), repr(self.value))

class node:
    def __init__(self, *args, **kwargs):
        self.args = args
        self.kvs = kwargs
    
    def __getitem__(self, key):
        return self.args[key]
    
    def __getattr__(self, key):
        return self.kvs[key]
    
    def __eq__(self, other):
        return self.args == other.args and self.kvs == other.kvs
    
    def __repr__(self):
        fmtstring = type(self).__name__ + "("
        fmtstring += ", ".join(["{}"] * len(self.args) + [key + "={}" for key in self.kvs.keys()])
        fmtstring += ")"
        
        return fmtstring.format(*map(repr, self.args + tuple(self.kvs.values())))

class Number(node): pass
class Plus(node): pass
class Minus(node): pass
class Times(node): pass
class Div(node): pass
class Sqrt(node): pass

class LexError(Exception): pass

def lex(chars):
    rules = [{'token':'number', 'regex':re.compile(r'(\d+)?\.\d+|\d+')},
                {'token':'sqrt', 'regex':re.compile(r'sqrt')},
                {'token':'lparen', 'regex':re.compile(r'\(')},
                {'token':'rparen', 'regex':re.compile(r'\)')},
                {'token':'plus', 'regex':re.compile(r'\+')},
                {'token':'minus', 'regex':re.compile(r'\-')},
                {'token':'times', 'regex':re.compile(r'\*')},
                {'token':'div', 'regex':re.compile(r'\/')},
                {'token':'-whitespace', 'regex':re.compile(r'\s+')},]
    
    chars = chars
    position = 0
    result = list()
    done = False
    
    while not done:
        done = True
        
        for rule in rules:
            match = re.match(rule['regex'], chars[position:])
            
            if match != None:
                if rule['token'][0] != '-':
                    result.append(token(rule['token'], match.group(0), position))
                
                position += len(match.group(0))
                done = False
                break
        
        if position < len(chars) and done:
            raise LexError("Invalid character at position {}".format(position))
    
    return result

class ParseError(Exception): pass

def parse(tokens):
    position = 0
    
    def current():
        nonlocal tokens, position
        
        if position >= len(tokens):
            return token('$eof', None, -1)
        else:
            return tokens[position]
    
    def next():
        nonlocal tokens, position
        position += 1
    
    def eat(tpe):
        if current().tpe != tpe:
            raise ParseError("Parse error at offset {} (expected {} but found {})".format(current().offset, tpe, current().tpe))
        
        result = current()
        next()
        return result
    
    def Expr():
        result = Factor()
        
        while current().tpe == "plus" or current().tpe == "minus":
            if current().tpe == "plus":
                next()
                result = Plus(lhs=result, rhs=Factor())
            else:
                next()
                result = Minus(lhs=result, rhs=Factor())
        
        return result
    
    def Factor():
        result = Atom()
        
        while current().tpe == "times" or current().tpe == "div":
            if current().tpe == "times":
                next()
                result = Times(lhs=result, rhs=Atom())
            else:
                next()
                result = Div(lhs=result, rhs=Atom())
        
        return result
    
    def Atom():
        minuses = 0
        result = None
        
        while current().tpe == "minus":
            minuses += 1
            next()
        
        if current().tpe == "lparen":
            eat("lparen")
            result = Expr()
            eat("rparen")
        elif current().tpe == "sqrt":
            eat("sqrt")
            eat("lparen")
            result = Sqrt(Expr())
            eat("rparen")
        else:
            result = Number(eat("number").value)
        
        if (minuses % 2) == 1:
            if type(result) == Number:
                return Number('-' + result[0])
            else:
                return Minus(lhs=Number('0'), rhs=result)
        else:
            return result
    
    return Expr()

def evaluate(root, numberize=False):
    result = None
    
    if type(root) == Number:
        result = float(root[0])
    elif type(root) == Plus:
        lhs = root.lhs if type(root.lhs) == Number else evaluate(root.lhs, True)
        rhs = root.rhs if type(root.rhs) == Number else evaluate(root.rhs, True)
        result = float(lhs[0]) + float(rhs[0])
    elif type(root) == Minus:
        lhs = root.lhs if type(root.lhs) == Number else evaluate(root.lhs, True)
        rhs = root.rhs if type(root.rhs) == Number else evaluate(root.rhs, True)
        result = float(lhs[0]) - float(rhs[0])
    elif type(root) == Times:
        lhs = root.lhs if type(root.lhs) == Number else evaluate(root.lhs, True)
        rhs = root.rhs if type(root.rhs) == Number else evaluate(root.rhs, True)
        result = float(lhs[0]) * float(rhs[0])
    elif type(root) == Div:
        lhs = root.lhs if type(root.lhs) == Number else evaluate(root.lhs, True)
        rhs = root.rhs if type(root.rhs) == Number else evaluate(root.rhs, True)
        result = float(lhs[0]) / float(rhs[0])
    elif type(root) == Sqrt:
        arg = root[0] if type(root[0]) == Number else evaluate(root[0], True)
        result = math.sqrt(float(arg[0]))
    
    if numberize:
        return Number(result)
    else:
        return result

def pprint(root, depth=0):
    result = ""
    
    if type(root) == Number:
        result = str(float(root[0]))
    elif type(root) == Plus:
        lhs = root.lhs if type(root.lhs) == str else pprint(root.lhs, depth+1)
        rhs = root.rhs if type(root.rhs) == str else pprint(root.rhs, depth+1)
        result = "({} + {})".format(lhs, rhs)
    elif type(root) == Minus:
        lhs = root.lhs if type(root.lhs) == str else pprint(root.lhs, depth+1)
        rhs = root.rhs if type(root.rhs) == str else pprint(root.rhs, depth+1)
        result = "({} - {})".format(lhs, rhs)
    elif type(root) == Times:
        lhs = root.lhs if type(root.lhs) == str else pprint(root.lhs, depth+1)
        rhs = root.rhs if type(root.rhs) == str else pprint(root.rhs, depth+1)
        result = "({} * {})".format(lhs, rhs)
    elif type(root) == Div:
        lhs = root.lhs if type(root.lhs) == str else pprint(root.lhs, depth+1)
        rhs = root.rhs if type(root.rhs) == str else pprint(root.rhs, depth+1)
        result = "({} / {})".format(lhs, rhs)
    elif type(root) == Sqrt:
        arg = root[0] if type(root[0]) == str else pprint(root[0], depth+1)
        result = "sqrt({})".format(arg)
    
    if depth == 0 and result[0] == "(":
        return result[1:-1] # get rid of outermost parenthesis
    
    return result
