#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# TODO: load/cache more pages
# TODO: rename "cut" / "pct_cut" into something more sensible
# TODO: lots of filters / search features
# TODO: use categories
# TODO: more sources
# TODO: place source in separate files

import random
import shlex
import getopt
import time
import threading

from plugins.parsingplugintemplate import ParsingPluginTemplate

from libs.libdeals.sources.steamdeals import steamdeals
from libs.libdeals.sources.gogdeals import gogdeals
from libs.libdeals.sources.humbledeals import humbledeals

class DealsPlugin(ParsingPluginTemplate):
    """
        config vars with defaults:

        [deals]
        ; command name
        command = "deals"

        ; lifetime in seconds of a cached web request
        webpage_cache_ttl_seconds = 3600

        ; maximum number of scraped pages per source
        scrape_page_limit = 4

        ; seconds to sleep before scraping each source again
        scrape_interval_seconds = 600

        ; seconds to delay between sources when scraping
        loader_sleep_seconds = 1
    """
    def __init__(self, bot):
        self._config = dict()

        super(DealsPlugin, self).__init__(bot, command=self._config.get('command', 'deals'), description="Finds products on sale.")

        # NOTE/TODO: currently not threadsafe to add or remove entries from .dealfinders
        # TODO: sources configurable in settings
        self._dealfinders = [steamdeals(logger=self), gogdeals(logger=self), humbledeals(logger=self)]

        for finder in self._dealfinders:
            finder.set_default_webpage_cache_ttl(int(self._config.get('webpage_cache_ttl_seconds', 3600)))
            finder.set_scrape_page_limit(int(self._config.get('scrape_page_limit', 4)))

        # .dealfinders_mutex should be obtained before interacting with any of the deal sources
        self._dealfinders_mutex = threading.Lock()

        # used by the background loader to ignore timer ticks until ready to load again
        self._next_load = 0

        def loader(timeval):
            if timeval < self._next_load:
                return


            # TODO: configurable sleep (600) here
            self._next_load = timeval + int(self._config.get('scrape_interval_seconds', 600))

            for finder in self._dealfinders:
                with self._dealfinders_mutex:
                    # self.log('loading deals from {}'.format(str(finder)))
                    finder.load_more_deals()

                time.sleep(float(self._config.get('loader_sleep_seconds', 1.0)))

        bot.add_event_listener('on_timer_tick', loader)

    def parse(self, msg):
        """
        usage:

        !deals                  get random deal
        !deals <string>         search for deals that contain the string
        !deals <decimal>        search for deals that are cheaper than the decimal number given
        !deals (-a, --all)      get list of all deals
        """


        text = msg.get_text()

        opts, nonopts = getopt.getopt(shlex.split(text), 'ha', ['help', 'all'])

        all = False

        if len(nonopts) > 0:
            search = True
            searchString = ' '.join(nonopts)
        else:
            search = False
            searchString = ''

        for opt in opts:
            if opt[0] == '-h' or opt[0] == '--help':
                return self.parse.__doc__
            elif opt[0] == '-a' or opt[0] == '--all':
                all = True

        deals = list()

        with self._dealfinders_mutex:
            for finder in self._dealfinders:
                deals += finder.get_deals()

        dealfmt = lambda deal: '[{source}] {title} (-{cut:.0f}%: {currency}{price_current:.2f}) - {url}'.format(
                                    source=deal.source.name, title=deal.title, cut=deal.cut*100, currency=deal.currency,
                                    price_current=deal.price_current, url=deal.url)

        alldealfmt = lambda deal: '    {title} (-{cut:.0f}%: {currency}{price_current:.2f})\n        {url}\n'.format(
                                    title=deal.title, cut=deal.cut*100, currency=deal.currency,
                                    price_current=deal.price_current, url=deal.url)

        if all or search:
            ans = list()
            oldsource = ''

            try:
                price = float(searchString)
            except:
                price = None

            for deal in sorted(deals, key=lambda deal: deal.source.name + str(2.0 - deal.cut)):
                if search and not price and not searchString.lower() in deal.title.lower():
                    continue
                if search and price and price < deal.price_current:
                    continue

                if deal.source.name != oldsource:
                    oldsource = deal.source.name
                    ans.append(deal.source.name)

                ans.append(alldealfmt(deal))

            if len(ans) == 0:
                if search:
                    ans.append('No deals matched the query')
                else:
                    ans.append('No deals available')

            ans = '\n'.join(ans)

            return self._bot.get_service("paste").paste(ans, msg)
        else:
            return dealfmt(random.choice(deals))
