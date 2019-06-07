#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# Created by lur
# Improved by lie


import shlex

from plugins.parsingplugintemplate import ParsingPluginTemplate
import libs.libcalc
from libs.janteparse import JanteParser, ArgumentParserError 

class CalcPlugin(ParsingPluginTemplate):
    def __init__(self, bot, description='Calculator / Computer Algebra System.'):
        super(CalcPlugin, self).__init__(bot, command="calc", description=description)
        
        self._argparser = JanteParser(description='A very basic calculator.', prog='calc', add_help=False)
        
        self._argparser.add_argument('-h', '--help', default=False, action='store_true', help="Show this help message")
        self._argparser.add_argument('--only-answer', '--raw',  action='store_true', help="Only return the answer.")
        self._argparser.add_argument('-t', '--tree', default=False, action='store_true', help="Display the parse tree of the expression.")
        self._argparser.add_argument('-i', '--int', default=False, action='store_true', help="Floor result to integer.")
        self._argparser.add_argument('expression', nargs="*", help="The expression that is to be evaluated.")

    def parse(self, message):
        try: 
            args = self._argparser.parse_args(shlex.split(message.get_text(), posix=False))
        except ArgumentParserError as error:
            return ArgumentParserError("\n{}".format(error))
        
        if args.help:
            return self._argparser.format_help()
        
        if not args.expression:
            return self._argparser.format_usage()
        
        tree = libs.libcalc.parse(libs.libcalc.lex(" ".join(args.expression)))
        value = libs.libcalc.evaluate(tree)
        
        if args.int:
            value = int(value)
        
        if args.only_answer:
            return str(value)
        elif args.tree:
            return libs.libcalc.pprint(tree) + ' = ' + str(value)
        else:
            return " ".join(args.expression) + ' = ' + str(value)
