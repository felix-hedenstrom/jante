#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
@Author sork
@Maintainers sork, Felix Hedenström, lur 

Depends on www.acronymfinder.com
"""
import re
import requests
import urllib.request
import html

from plugins.plugintemplate import PluginTemplate

class Acronym(PluginTemplate):
    def __init__(self, bot):
        super().__init__(bot, description= "Returns an acronym.")
        bot.add_command_listener('acronym', self.parse, strip_preamble=True)

    def acronym(self, s):
        lookup = s.lower()
        headers = {'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_10_1) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/39.0.2171.95 Safari/537.36'}
        htmlresponse = requests.get('https://www.acronymfinder.com/' + str(lookup) + '.html', headers=headers , timeout=0.75)
        response = re.findall(r'goog_search\(\'([^\']+)', htmlresponse.content.decode())

        alternatives = list(set(map(lambda r: html.unescape(r.replace("+", ' ')).lower(), response)))
        results = []
        for a in alternatives:
            tmp = a.split(" ")
            tmpnew = ""
            for t in tmp:
                tmpnew += t.title() + " "
            results.append(tmpnew)

        if len(results) == 0:
            return 'No acronyms were found for "{}".'.format(s.upper())

        ans = '"{}" is an acronym for:\n{}'.format(s.upper(), "\n".join(results[:3]))
        if len(alternatives) >= 3:
            ans += '\nAnd {} more: {}'.format(len(alternatives) - 3, self._bot.get_service("paste").paste("\n".join(results)))

        return ans

    def parse(self, message):
        if len(message.get_text().strip()) == 0:
            ans = RuntimeError("Must supply an acronym to find.")
        else:
            ans = self.acronym(message.get_text().strip())

        self.send_message(message.respond(ans, self._bot.get_nick()))
