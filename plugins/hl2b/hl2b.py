#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import re
import requests

from plugins.parsingplugintemplate import ParsingPluginTemplate

class HL2BPlugin(ParsingPluginTemplate):
    class HL2BEntry:
        def __init__(self, name):
            self.name = name
            self.tidbits = dict()

        def add_tidbit(self, title, time):
            self.tidbits[title] = time

        def __repr__(self):
            return 'HL2BEntry({}, {})'.format(self.name, str(self.tidbits))

        def __str__(self):
            return '{} - {}'.format(self.name, str(self.tidbits).replace("'", ""))

    def __init__(self, bot):
        super(HL2BPlugin, self).__init__(bot, command="hl2b", description='Queries howlongtobeat.com')

    #https://howlongtobeat.com/search_main.php?page=1
    def search(self, query):
        try:
            the_url = 'https://howlongtobeat.com/search_results.php?page=1'

            headers = {'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_10_1) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/72.0.3626.109 Safari/537.36'}

            data = {
                'queryString': query,
                't': 'games',
                'sorthead': 'popular',
                'sortd': 'Normal Order',
                'plat': '',
                'length_type': 'main',
                'length_min': '',
                'length_max': '',
                'detail': ''
            }

            response = requests.post(the_url, headers=headers, data=data, timeout=10.0)

            html = response.content.decode('utf-8')

            html_items = re.findall(r'<li.+?</li>', html, re.DOTALL)

            results = list()

            for item in html_items:
                try:
                    thisresult = self.HL2BEntry(re.search(r'a title="([^"]+)', item).group(1))

                    tidbits = re.findall(r'search_list_tidbit[^>]+>([^<]+)</div>', item)

                    i = 0
                    while i < len(tidbits):
                        thisresult.add_tidbit(tidbits[i].strip(), tidbits[i+1].strip().replace('&#189;', '.5'))
                        i += 2

                    results.append(thisresult)
                except Exception as e:
                    # print(e)
                    continue

            return results
        except:
            return None

    def parse(self, message):
        text = message.get_text()

        if '-h' in text or '--help' in text or text == '':
            return 'Usage: !hl2b <game name>'

        results = self.search(text)

        if len(results) > 0:

            ans = "{}.".format(results[0])
            if len (results) > 1:
                ans += " More:\n {}".format(self._bot.get_service("paste").paste("\n".join(map(str, results[1:]))))
            return ans
        else:
            return 'No results'
