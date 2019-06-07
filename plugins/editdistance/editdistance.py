#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import threading
import traceback
import random
import re
import shlex
import getopt
import json

from plugins.parsingplugintemplate import ParsingPluginTemplate

import libs.nlp.similar as similar

class EditDistancePlugin(ParsingPluginTemplate):
    """
    Handle all your copypasta with this simple plugin
    !ed (-h, --help)

    !ed "<phrase1>" "<phrase2>"

    !ed [-n <options>] <arg> <phrase>
        (-d, --dict, -l, --lang) <dictlang>
            Use a swedish or english dictionary. Use "se" or "en" to pick dictionary.
        (-g, --gen)
        (-e) [(-d, --dict, -l, --lang) <dictlang>] <phrase>
            Evaluate the phrase.
    """
    def __init__(self, bot):
        super(EditDistancePlugin, self).__init__(bot, command="ed", description="Calculate the edit distance between words!")
    
    def _compare(self, word1, word2):
        return 'The levenshtein distance between "{}" and "{}" is {}.'.format(word1, word2, int(similar.levenshtein(word1, word2)))
        
    def parse(self, message):
        argv = shlex.split(message.get_text())
        try:
            opts, nonopts = getopt.getopt(argv, 'hn:',
            ["help"])
        except:
            return "Not a valid option. Please try another or check out !ed --help"
        n = 10
        for opt in opts:
            if opt[0] == '-n':
                try:
                    n = int(opt[1])
                except:
                    return 'Could not parse "{}" into an integer.'.format(opt[1])

            if opt[0] == '-h' or opt[0] == '--help':
                return self._bot.get_service("paste").paste(self.__doc__, message)
        
        if len(nonopts) == 1:
            return "Must contain more than one word/phrase."

        if len(nonopts) == 2:
            tmp = list(map(lambda x: x.strip(), nonopts))
            return self._compare(tmp[0], tmp[1])
        else:
            return '"{}" is similar to "{}".'.format(nonopts[0], '", "'.join(similar.possibilities(nonopts[0], nonopts[1:], alternatives=n, subsets=False)))

        return RuntimeError("Something went wrong.")
