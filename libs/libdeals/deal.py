#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import datetime

from .source import source as libsource
from .typecheck import instanceof
from .typecheck import fn_apply as typecheck_fn

class deal:
    def __init__(self, source, title, url, currency, price_normal, price_current, cut, categories=[]):
        self.source = instanceof(source, libsource, name='source')
        self.title = typecheck_fn(title, lambda x: str(x), name='title', suggest=str)
        self.url = typecheck_fn(url, lambda x: str(x), name='url', suggest=str)
        self.currency = typecheck_fn(currency, lambda x: str(x), name='currency', suggest=str)
        self.price_normal = typecheck_fn(price_normal, lambda x: float(x), name='price_normal', suggest=float)
        self.price_current = typecheck_fn(price_current, lambda x: float(x), name='price_current', suggest=float)
        self.cut = typecheck_fn(cut, lambda x: float(x), name='cut', suggest=float)
        
        self.time_first_seen = datetime.datetime.now()
        self.time_seen = None
        self.time_expires = None
        self.refresh()
        
        assert self.cut >= 0 and self.cut <= 1, 'cut must be in range [0..1]'
        
        self.set_categories(categories)
    
    def refresh(self):
        self.time_seen = datetime.datetime.now()
        
        # TODO: configurable ttl?
        self.time_expires = self.time_seen + datetime.timedelta(seconds=3600)
    
    def is_expired(self):
        return datetime.datetime.now() >= self.time_expires
    
    def set_categories(self, categories):
        self.categories = typecheck_fn(categories, lambda x: list(map(lambda y: str(y), x)), name='categories', suggest='list() of str')
    
    def add_category(self, category):
        self.categories.append(category)
    
    def __repr__(self):
        return 'deal(source={source}, title={title}, url={url}, currency={currency}, price_normal={price_normal}, price_current={price_current}, cut={cut}, categories={categories}, seen={seen}, expires={expires})'.format(
            source=self.source, title=self.title, url=self.url, currency=self.currency, price_normal=self.price_normal,
            price_current=self.price_current, cut=self.cut, categories=self.categories,
            seen=str(self.time_seen), expires=str(self.time_expires))
    
    def __eq__(self, other):
        return (self.source == other.source
            and self.title == other.title
            and self.url == other.url
            and self.currency == other.currency
            and self.price_normal == other.price_normal
            and self.price_current == other.price_current
            and self.cut == other.cut)
    
    def __hash__(self):
        hash = 17
        
        for c in self.url:
            hash = hash * 31 + ord(c)
        
        return hash
