#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
@Author Felix Hedenström
Created 14-04-2018
"""

from plugins.plugintemplate import PluginTemplate
import libs.nlp.similar

class NonCommandTrackerPlugin(PluginTemplate):
    def __init__(self, bot):
        super().__init__(bot, description="Keeps track of when users call for non-existing commands.")

        def ffilter(message):

            text = message.get_text().strip()

            if not text[0] == self._bot.get_command_prefix():
                return False

            if text[1:].split(" ")[0] in self._bot.get_commands().keys():
                return False

            return True

        self._bot.add_event_listener('on_message', self.respond, prefilter=ffilter )

    def respond(self, message):

        text = message.get_text().strip()

        text = text[1:]
        command = text.split(" ")[0]
        self.log('Found a non-existing command: "{}."'.format(command))

        returnmessagetext = 'Command "{prefix}{command}" was not found. Try using "{prefix}commands" for a list of commands.'.format(command=command, prefix=self._bot.get_command_prefix())

        if True: # TODO make this configurable
            commands = '", "{prefix}'.join(libs.nlp.similar.possibilities(command, list(self._bot.get_commands().keys()))).format(prefix=self._bot.get_command_prefix())
            returnmessagetext += '\nCould you have ment: "{prefix}{commands}"?'.format(commands=commands, prefix=self._bot.get_command_prefix())

        ans = message.respond(RuntimeError(returnmessagetext), self._bot.get_nick())

        self._bot.add_message(ans)
