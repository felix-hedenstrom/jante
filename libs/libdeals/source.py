#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import datetime
import requests
import sys
import traceback

from .typecheck import instanceof
from .typecheck import fn_apply as typecheck_fn

import libs.libdeals

class source:
    class cache_entry:
        def __init__(self, content, ttl):
            self.content = typecheck_fn(content, lambda x: str(x), name='content', suggest=str)
            self.expires = datetime.datetime.now().timestamp() + typecheck_fn(ttl, lambda x: float(x), name='ttl', suggest=float)
        
        def is_expired(self):
            return datetime.datetime.now().timestamp() >= self.expires
    
    def __init__(self, name, title, url, logger=None):
        self.name = typecheck_fn(name, lambda x: str(x), name='name', suggest=str)
        self.title = typecheck_fn(title, lambda x: str(x), name='title', suggest=str)
        self.url = typecheck_fn(url, lambda x: str(x), name='url', suggest=str)
        self.deals = list()
        self.webpage_cache = dict()
        self.logger = logger
        self._webpage_timeout = 10.0
        self._webpage_cache_ttl = 3600
        self._scrape_page_limit = 4
    
    def set_default_webpage_timeout(self, timeout):
        self._webpage_timeout = timeout
    
    def set_default_webpage_cache_ttl(self, ttl):
        self._webpage_cache_ttl = ttl
    
    def set_scrape_page_limit(self, limit):
        self._scrape_page_limit = limit
    
    def get_scrape_page_limit(self):
        return self._scrape_page_limit
    
    def get_deals(self):
        size_before = len(self.deals)
        self.deals = list(filter(lambda x: not x.is_expired(), self.deals))
        size_after = len(self.deals)
        
        # self.log('expiration prune delta: {}'.format(size_after - size_before))
        
        return self.deals
    
    def load_more_deals(self):
        raise NotImplementedError()
    
    def add_deal(self, title, url, currency, price_normal, price_current, pct_cut, categories=[]):
        thedeal = libs.libdeals.deal(self, title, url, currency, price_normal, price_current, pct_cut, categories)
        
        if thedeal in self.deals:
            self.deals[self.deals.index(thedeal)].refresh()
            # self.log('refreshed deal {}'.format(url))
        else:
            self.deals.append(thedeal)
            # self.log('added deal {}'.format(url))
    
    def get_webpage(self, url, timeout=None, cache_ttl=None, cookies={}):
        if timeout == None:
            timeout = self._webpage_timeout
        
        if cache_ttl == None:
            cache_ttl = self._webpage_cache_ttl
        
        if url in self.webpage_cache and not self.webpage_cache[url].is_expired():
            # self.log('returning cache for {}'.format(url))
            return self.webpage_cache[url].content
        
        try:
            # self.log('fetching {}'.format(url))
            
            headers = {'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_10_1) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/39.0.2171.95 Safari/537.36'}
            html = requests.get(url, headers=headers , timeout=timeout, cookies=cookies)
            content = html.content.decode('utf-8')
            self.webpage_cache[url] = self.cache_entry(content, cache_ttl)
            return content
        except Exception as e:
            self.log_exception(e)
            return None
    
    def log(self, s):
        if self.logger != None:
            self.logger.log('(deals.source) [{}/{}] - {}'.format(self.name, self.title, str(s)))
    
    # TODO: get rid of "e" parameter
    def log_exception(self, e):
        self.log('exception: ' + traceback.format_exc())
