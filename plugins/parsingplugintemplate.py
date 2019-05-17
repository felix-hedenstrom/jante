#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
@Author Felix Hedenström
A basic template that allow parsing.

Plugins that has functionallity that use user input will benifit from this template.

Classes that inherit from this method is expected to have a method called 'parse' which accepts a JanteMessage object.
"""

import re
import traceback
from abc import ABCMeta, abstractmethod

from plugins.plugintemplate import PluginTemplate
from libs.jantemessage import JanteMessage

class ParsingPluginTemplate(PluginTemplate):
    def __init__(self, bot, description="This plugin does not yet have a description", command=None):
        
        if command != None:
            bot.add_command_listener(command, self.parsewrap, strip_preamble=True)
        else:
            raise Exception("A parsingbotplugin called super constructor without a command.")
        
        super().__init__(bot, description=description)
        self._command = command
    
    def parsewrap(self, message):
        # If the plugin fails during its exicution, return the error
        try:
            result = self.parse(message)
        
        except Exception as e:
            errormsg = traceback.format_exc()
            post_link = self.error_with_post('{}\nError while parsing in plugin "{}."'.format(errormsg, self.__class__.__name__))
            
            self.send_message(message.respond(Exception('Error in "{}"-plugin parse method. See {}'.format(self.__class__.__name__, post_link)), self.__class__.__name__))
            return
        # If the message was ment for a user but is empty, report it as an error just in case.
        if not message.is_internal() and result == "":
            self.send_message(message.respond(RuntimeError("{} returned an empty string.".format(self.__class__.__name__)), self.__class__.__name__))
        # If the plugin returned an error
        elif issubclass(type(result), BaseException):
            self.send_message(message.respond(result, self.__class__.__name__))
        # If the plugin returned something that was not a string, report it as an error
        elif not type(result) == str:
            self.send_message(message.respond(RuntimeError("{} returned a non-string of type {}.".format(self.__class__.__name__, type(result))), self.__class__.__name__))
        else:
            self.send_message(message.respond(result, self.__class__.__name__))
    
    def parse(self, message):
        pass
