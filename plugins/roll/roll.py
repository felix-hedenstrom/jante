#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import random

import shlex


if __name__ == '__main__':
    import sys
    sys.path.append('../..')
    sys.path.append('../../libs')

from plugins.parsingplugintemplate import ParsingPluginTemplate

import libs.janteparse as janteparse 


class RollPlugin(ParsingPluginTemplate):
    """
        roll is the default command for this plugin.

        roll
            Returns a number between 1 and n. n is confiured in the settingsfile and is by default 6.
        roll <integer>
            Returns a number between 1 and the specified integer.
        roll help
            Shows help.

        roll <word1> <word2> ...
            Picks a random word
    """
    def __init__(self, bot):

        super().__init__(bot, command="roll", description="Returns a diceroll.")

        self.parser = janteparse.JanteParser(description='Random number generation!', prog="roll", add_help=False)
        group = self.parser.add_mutually_exclusive_group()

        group.add_argument('-h', '--help', action='store_true', required=False, help="Shows this helpful message.")
        group.add_argument('-n', '--newline', action='store_true', required=False, help="Splits at newline instead of at space and quations.")

        self.parser.add_argument('items', nargs="*", help="""Items to roll between. If it is of type integer, roll a number between 1 and the supplied integer.
        If it is a list of items, pick one of the items. The items can be sperated by space or by using quotationmarks. If the -n option is used items are split up by newlines.""")

    def parse(self, message):
        # Doubleparse, to check for -n option before shlexing
        try:
            args = self.parser.parse_args(message.get_text().split(" "))
        except Exception as e:

            return janteparse.ArgumentParserError("\n{}".format(e))

        if args.newline:
            items = message.get_text().split("\n")#[1:]
            items[0] = " ".join(items[0].split(" ")[1:])
            if items[0].strip() == "" and len(items) == 1:
                items = []
        else:
            try:
                args = self.parser.parse_args(shlex.split(message.get_text()))

            except Exception as e:

                return janteparse.ArgumentParserError("\n{}".format(e))
            items = args.items
        if __debug__:
            self.log("Alternatives: {}".format(items))
        if args.help:
            return self.parser.format_help()

        if len(items) > 1 or args.newline:
            if len(items) == 0:
                return RuntimeError("Can't pick between 0 items. {}".format(self.parser.format_usage()))
            return random.choice(items)

        if len(items) == 0:
            d = int(6) # default to 6
        else:
            try:
                d = int(items[0])
            except:
                return ValueError("Must be an integer. \"{}\" is a {}.".format(items[0], type(items[0])))

        roll = random.randint(1,d)
        return str(roll)
