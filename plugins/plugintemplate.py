#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
@Author Felix Hedenström
A base plugin. Contains the most basic features a plugin can have.
Does not automatically support parsing, which means such functionallity has to be manually added or any plugin inheriting directly from PluginTemplate should not be directly interactive, e.g. a logger or something that only sends things to users without being able to recieve.
"""


import sys
import traceback
from abc import ABCMeta, abstractmethod

class PluginTemplate(object):
    def __init__(self, bot, description="NoDescription"):
        self._description = description
        self._bot = bot
    
    def _format_log(self, text):
        return "{}::{}".format(self.__class__.__name__, text)
    
    def get_description(self):
        return self._description
    
    def error(self, text):
        self._bot.error(self._format_log(text))
    
    def error_with_post(self, text):
        self.error(text)
        return self._bot.get_service("paste").paste(text)
    
    def log(self, *text):
        for t in text:
            self._bot.log(self._format_log(t))
    
    def debuglog(self, *text):
        if __debug__:
            for t in text:
                self.log("DEBUG::{}".format(self._format_log(t)))
    def debug(self, *text):
        self.debuglog(text)
        
    def send_message(self, message):
        self._bot.add_message(message)
