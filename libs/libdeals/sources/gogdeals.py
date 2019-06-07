#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import json

from .. import source

class gogdeals(source):
    def __init__(self, logger=None):
        super().__init__('GOG', 'Discounted', 'https://www.gog.com/games?price=discounted&sort=popularity&page=1', logger=logger)
        self.page = 0
    
    def load_more_deals(self):
        cookies = {'gog_lc':'SE_EUR_en-US'}
        url = 'https://www.gog.com/games/ajax/filtered?mediaType=game&page={page}&price=discounted&sort=popularity'.format(page=self.page + 1)
        html = self.get_webpage(url, cookies=cookies)
        
        try:
            deal_added = False
            gogdata = json.loads(html)
            # self.log('{} products found'.format(len(gogdata['products'])))
            
            for p in gogdata['products']:
                deal_added = True
                self.add_deal(p['title'], 'http://www.gog.com' + p['url'], p['price']['symbol'],
                    p['price']['baseAmount'], p['price']['amount'], float(p['price']['discountPercentage']) / 100.0)
            
            if deal_added:
                self.page = (self.page + 1) % self.get_scrape_page_limit()
            else:
                self.page = 0
        except Exception as e:
            self.log_exception(e)
