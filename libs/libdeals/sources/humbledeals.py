#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import json

from .. import source

class humbledeals(source):
    def __init__(self, logger=None):
        super().__init__('Humble', 'On Sale', 'https://www.humblebundle.com/store/search?sort=discount&filter=onsale', logger=logger)
        self.page = 0
    
    def load_more_deals(self):
        html = self.get_webpage('https://www.humblebundle.com/store/api/search?sort=discount&filter=onsale&request=1&page_size=20&page={page}'.format(page=self.page))
        
        try:
            deal_added = False
            jsonObj = json.loads(html)
            
            # self.log('{} products found'.format(len(jsonObj['results'])))
            
            for entry in jsonObj['results']:
                title = entry['human_name']
                url = 'https://www.humblebundle.com/store/' + entry['human_url']
                
                if not 'full_price' in entry:
                    continue
                
                currency = entry['full_price'][1]
                price_normal = entry['full_price'][0]
                price_current = entry['current_price'][0]
                
                if float(entry['full_price'][0]) > 0:
                    cut = 1.0 - float(entry['current_price'][0]) / float(entry['full_price'][0])
                else:
                    cut = 0.0
                
                self.add_deal(title, url, currency, price_normal, price_current, cut)
                deal_added = True
            
            if deal_added:
                self.page = (self.page + 1) % self.get_scrape_page_limit()
            else:
                self.page = 0
        except Exception as e:
            self.log_exception(e)
