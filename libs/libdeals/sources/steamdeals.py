#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import re

from .. import source

class steamdeals(source):
    def __init__(self, logger=None):
        super().__init__('Steam', 'Steam Specials', 'http://store.steampowered.com/search/?category1=998&specials=1', logger=logger)
        self.page = 0
    
    def load_more_deals(self):
        deal_added = False
        html = self.get_webpage('http://store.steampowered.com/search/?category1=998&specials=1&page={page}'.format(page=self.page + 1))
        r = re.compile('(?P<full><a\s+href="(?P<url>https?://store.steampowered.com/app[^"]+)".+?(?P<cut>-\d+)%.+?(?P<price>[\d,]+)(?P<currency>$|€))', re.DOTALL)
        
        products_found = 0
        
        try:
            for match in [m.groupdict() for m in r.finditer(html)]:
                spans = re.findall(r'(<span[^>]+>(.*?)</span)', match['full'], re.DOTALL)
                
                title = None
                
                for snippet in spans:
                    if len(snippet) >= 2 and 'title' in snippet[0] and len(snippet[1]) > 0:
                        title = snippet[1]
                        break
                
                if title == None:
                    title = re.search(r'app/\d+/([^/]+)', match['url'])
                    
                    if title == None:
                        title = match['url']
                    else:
                        title = title.group(1)
                
                match['url'] = re.sub(r'(\?|&)?snr=[0-9_]+', '', match['url'])
                
                price = float(re.sub(r'[^\d]', '.', match['price'])) # assuming match['price'] of form "\d+,\d+"
                cut = float(re.sub(r'[^\d]', '', match['cut'])) / 100.0 # assuming match['cut'] of form "-?\d+%?"
                
                self.add_deal(title, match['url'], match['currency'], price, price * (1.0 - cut), cut)
                deal_added = True
                products_found += 1
            
            # self.log('{} products found'.format(products_found))
        except Exception as e:
            self.log_exception(e)
        
        if deal_added:
            self.page = (self.page + 1) % self.get_scrape_page_limit()
        else:
            self.page = 0
