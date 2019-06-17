#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
@Author Felix Hedenström, sork
"""
import random
import argparse

import re
import traceback

from plugins.parsingplugintemplate import ParsingPluginTemplate

vowels = ["a", "e", "ü", "i", "o", "u", "y", "å", "ä", "ö"]
punctuation = [".", "!", "?"]

inflationary_dict = {
    "se":

    [
        ["noll", "ingen", "intet", "0"],
        ["en", "ett", "1"],
        ["två", "2", "tu", "duo"],
        ["tre", "3", "trio", "trippel"],
        ["fyra", "4"],
        ["fem", "5"],
        ["sex", "6"],
        ["sju", "7"],
        ["åtta", "8"],
        ["nio", "9"],
        ["tio", "10"],
        ["elva", "11"]
    ],

    "en":
    [
        ["zero", "0", "null", "none"],
        ["one", "1", "sole", "single", "uno"],
        ["two", "2"],
        ["three", "3"],
        ["four", "4", "for"],
        ["five", "5"],
        ["six", "6", "sex"],
        ["seven", "7"],
        ["eight", "8"],
        ["nine", "9"],
        ["ten", "11"],
        ["eleven", "11"]
    ]
}

class ObscurePlugin(ParsingPluginTemplate):
    
    def __init__(self, bot):
        super().__init__(bot, command="obscure", description="Obscure text.")

        self.parser = argparse.ArgumentParser(description='Obscure text.', prog='obscure', add_help=False)

        self.parser.add_argument('-h', '--help', action='store_true', required=False, help="Shows this helpful message.")

        self.parser.add_argument('-m', '--military', action='store_true', required=False, help="Prints the message in NATO phonetic alphabet.")
        self.parser.add_argument('-r', "-b", "--reverse", '--backwards', action='store_true', required=False, help="Prints the text backwards.")
        self.parser.add_argument("--rövarspråk", action='store_true', required=False, help="Translate the text to rövarspråk.")
        self.parser.add_argument('-p', '--piglatin', action='store_true', required=False, help="Translate the text to piglatin.")
        self.parser.add_argument('-l', '--last', action='store_true', required=False, help="Use the last thing posted in the chat.")
        self.parser.add_argument('-s', '--svinlatin', action='store_true', required=False, help="Translate the text to svinlatin.")
        self.parser.add_argument('-g', '--gibberish', action='store_true', required=False, help="Translate the text to Gibberish https://en.wikipedia.org/wiki/Gibberish_(language_game).")
        self.parser.add_argument('-i', '--inflationary', type=str, const="en", nargs="?", choices=['en', 'se'], help="Inflate the text https://en.wikipedia.org/wiki/Victor_Borge#Borge's_style")
        self.parser.add_argument('words', metavar='WORDS', type=str, nargs='*', help='Words that should be translated around.')
        #self.parser.add_argument("--izzle", action='store_true', required=False, help="Mizzle Chistmizzle! Make you text cooler.")

        self.parser.add_argument('--izzle', action='store_true', required=False, help="Make you text cooler.")

        self.last = ""
        self._bot.add_event_listener('on_message', self._last_listen)

    def _last_listen(self, message):
        if message.get_text().strip().startswith(self._bot.get_command_prefix()):
            return

        self.last = message.get_text()

    def reverse(self, text):
        return text[::-1]
    
    def military(self, text):
        charlist = list(text)
        res = ""
        letter = {97:"Alpha ", 98:"Bravo ", 99:"Charlie ", 100:"Delta ", 101:"Echo ", 102:"Foxtrot ", 103:"Golf ", 104:"Hotel ", 105:"India ", 106:"Juliett ", 107:"Kilo ", 108:"Lima ",
                 109:"Mike ", 110:"November ", 111:"Oscar ", 112:"Papa ", 113:"Quebec ", 114:"Romeo ", 115:"Sierra ", 116:"Tango ", 117:"Uniform ", 118:"Victor ", 119:"Whiskey ",
                  120:"Xray ", 121:"Yankee ", 122:"Zulu "}
        for char in charlist:
            num = 0
            if ord(char) == 32:
                res += "- "
            elif ord(char) > 64 and ord(char) < 90:
                num = (ord(char) + 32)
                res += letter[num]
            elif ord(char) < 64 or ord(char) > 122:
                continue
            else:
                num = ord(char)
            res += letter[num]
        return res


    def rovarspraket(self, text):
        ans = ""
        last = None
        for word in text.split():
            for char in word:
                tmp = ""
                if char == "x":
                    tmp = "koksos"
                elif char in vowels or char in punctuation:
                    tmp = char
                else:
                    tmp = char + "o" + char

                if last in punctuation:
                    tmp = tmp.title()
                if last == None:
                    ans = tmp.title()
                else:
                    ans += tmp
                last = char
            ans += " "
        return ans

    def piglatin(self, text, ending, altending):
        ans = ""
        #Nonempty to create capital letter in the beginning
        last = "---"

        for word in text.split():
            first = re.match("[^{}]*".format("".join(vowels)), word).group(0)

            middle = re.match("\w*".format("".join(punctuation)), word[len(first):]).group(0)

            if len(first) == 0:
                tmpending = altending
            else:
                tmpending = ending

            if len(last) == 0:
                ans += middle + first + tmpending
            else:
                ans += middle.title() + first + tmpending

            last = word[len(first) + len(middle):]

            ans += "{} ".format(last)

            last = re.match("[{}]*".format("".join(punctuation)), last).group(0)
        return ans

    def gibberish(self, text):
        alternatives = ["idig", "uddag", "uvug", "uthug"]
        ans = ""
        lastword = "."
        for word in text.split():
            tmp = ""
            last = "d" #Non vowel

            for char in word:
                if char in vowels and last not in vowels:
                    tmp += random.choice(alternatives) + char
                else:
                    tmp += char
                last = char

            if lastword[-1] in punctuation:
                ans += tmp.title()
            else:
                ans += tmp
            ans += " "
            lastword = word
        return ans

    def izzle(self, text):
        ans = ""
        for word in text.split():
            if len(word) > 3:
                match = re.search(r"([bcdfghjklmnpqrstvwx']+)[aeiouy]+[bcdfghjklmnpqrstvwx']*([^\w]+)?$", word)

                if match is None:
                    continue

                ans += word[0:match.span()[0]+1] + 'izzle'

                if match.span()[1] < len(word):
                    ans += word[match.span()[1]:]

                ans += ' '
            else:
                ans += word + " "

        return ans.capitalize()


    def inflationary(self, text, language):
        alternatives = inflationary_dict[language]
        ans = text
        for number in reversed(range(0, len(alternatives))):
            for sub_alternative in alternatives[number]:

                ans = ans.replace(sub_alternative, alternatives[(number + 1) % len(alternatives)][0])

        return ans.capitalize()


    def parse(self, message):
        try:
            args = self.parser.parse_args(message.get_text().split(" "))
        except ArgumentParserError as error:
            return ArgumentParserError("\n{}".format(error))
        
        if args.last:
            text = self.last
        else:
            text = " ".join(args.words)

        text = text.lower()


        if args.help:
            return self.parser.format_help()
        elif args.reverse:
            return self.reverse(text)
        elif args.military:
            return self.military(text)
        elif args.rövarspråk:
            return self.rovarspraket(text)
        elif args.piglatin:
            return self.piglatin(text, "ay", "way")
        elif args.svinlatin:
            return self.piglatin(text, "öff", "nöff")
        elif args.gibberish:
            return self.gibberish(text)
        elif args.inflationary:
            return self.inflationary(text, args.inflationary)

        elif args.izzle:
            return self.izzle(text)


        return "See --help to pick obscuration method."
