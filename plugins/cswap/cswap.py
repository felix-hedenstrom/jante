#!/usr/bin/env python3
# -*- coding: utf-8 -*-

if __name__ == '__main__':
    import sys
    sys.path.append('../..')
    sys.path.append('../../libs')

import random
import argparse

from plugins.plugintemplate import PluginTemplate
from plugins.cswap.spoon import spoon

class CSwapPlugin(PluginTemplate):
    class TestBuffer():
        def __init__(self):
            self.text = ""
        
        def write(self, text):
            self.text += text
        
        def to_string(self):
            return self.text
    
    def __init__(self, bot):
        super().__init__(bot, description="Consonant swapper, for your entertainment.")
        
        bot.add_command_listener('cswap', self.parse, strip_preamble=True)
        bot.add_command_listener('spoon', self.__spoon_wrapper, strip_preamble=True, direct_reply=True)
        
        self.parser = argparse.ArgumentParser(description='Swap characters around!', prog='cswap', add_help=False)
        self.parser.add_argument('-s', '--spoonerism', action='store_true', required=False, help="Create a spoonerism from WORDS. https://en.wikipedia.org/wiki/spoonerism")
        self.parser.add_argument('words', metavar='WORDS', type=str, nargs='*', help='Words that should be swapped around.')
        self.parser.add_argument('-h', '--help', action='store_true', required=False, help="Shows this helpful message.")
        self.parser.add_argument('-l', '--last', action='store_true', required=False, help="Use the last thing posted in the chat.")
        
        self.last = ""
        self._bot.add_event_listener('on_message', self._lastlisten)
    
    def _lastlisten(self, message):
        if message.get_text().strip().startswith(self._bot.get_config()['global']['prefix']):
            return
        
        self.last = message.get_text()
    
    def __spoon_wrapper(self, message):
        return spoon(message.get_text())
    
    def cswap(self, s):
        vows = 'aeiouyåäö'
        # cons = 'bcdfghjklmnpqrstvwxz'
        cons = 'bcdfghjklmnprstvwxz'
        
        candidates = list()
        s = s.lower()
        
        for i in range(0, len(s)):
            if s[i] in cons and not (i > 0 and s[i - 1] in cons) and i + 1 < len(s) and s[i + 1] in vows:
                candidates.append(i)
        
        if len(candidates) < 2:
            return None
        
        random.shuffle(candidates)
        prob = 1.0
        result = list(s)
        
        while len(candidates) >= 2:
            choice = [candidates.pop(), candidates.pop()]
            
            if result[choice[0]] == result[choice[1]]:
                if len(candidates) == 0:
                    break
                else:
                    success = False
                    
                    for i in range(0, len(candidates)):
                        if result[candidates[i]] != result[choice[1]]:
                            tmp = choice[1]
                            choice[1] = candidates[i]
                            candidates[i] = tmp
                            
                            success = True
                            break
                    
                    if not success:
                        break
            
            if random.random() > prob:
                continue
            
            tmp = result[choice[0]]
            result[choice[0]] = result[choice[1]]
            result[choice[1]] = tmp
        
        return ''.join(result)
    
    def parse(self, message):
        args = self.parser.parse_args(message.get_text().split(" "))
        
        if args.help:
            tb = CSwapPlugin.TestBuffer()
            self.parser.print_help(tb)
            ans = tb.to_string()
        elif args.spoonerism:
            if args.last:
                ans = spoon(self.last)
            else:
                ans = spoon(" ".join(args.words))
        else:
            if args.last:
                ans = self.cswap(self.last)
            else:
                ans = self.cswap(" ".join(args.words))
        
        self.send_message(message.respond(str(ans), self._bot.get_nick()))
