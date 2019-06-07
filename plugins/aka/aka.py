#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import re
import enum
import json
import shlex
import argparse
import io
import threading

from plugins.plugintemplate import PluginTemplate
from libs.jantemessage import JanteMessage

class AKAPlugin(PluginTemplate):
    class MyArgParser(argparse.ArgumentParser):
        def __init__(self, *args, **kwargs):
            self._state_error = False
            super().__init__(*args, **kwargs)
        
        def error(self, message):
            self._state_error = True
        
        def has_error(self):
            return self._state_error
        
        def reset_error(self):
            self._state_error = False
    
    def __init__(self, bot):
        super().__init__(bot, description="A.K.A - Also Known As. Implements command aliases")
        
        self._registry_mutex = threading.Lock()
        
        try:
            self._env_command_prefix = bot.getCommandPrefix()
        except:
            self._env_command_prefix = '!'
        
        if self._env_command_prefix is None:
            self._env_command_prefix = '!'
        
        try:
            self._config = bot.getConfig('aka')
        except:
            self._config = dict()
        
        self._aka_command = self._config.get('command', 'aka')
        self._registry_filename = bot.get_data_path('aka', self._config.get('filename',
                                                                            'akastorage.json'))
        
        self._registry = self._load_registry(self._registry_filename)
        
        if self._registry == None:
            self._registry = dict()
        
        self._register_commands_from_registry(self._registry)
        
        # TODO: a --list subcommand
        
        self._argparser = self.MyArgParser(description='A.K.A - Also Known As. Implements \
            command aliases', prog=self._aka_command, add_help=False)
        
        self._argparser.add_argument('-h', '--help', default=False, action='store_true',
            required=False, help="Show this help message")
        
        self._argparser.add_argument('-l', '--local', default=False, action='store_true',
            required=False, help="Work with an alias for yourself only")
        
        self._argparser.add_argument('-g', '--global', default=False, action='store_true',
            required=False, help="Work with a global alias")
        
        self._argparser.add_argument('-d', '--delete', default=False, action='store_true',
            required=False, help="Remove an alias")
        
        self._argparser.add_argument("alias", metavar="ALIAS", help="Command alias")
        self._argparser.add_argument("target", nargs=argparse.REMAINDER, metavar="TARGET",
            help="Command target")
        
        bot.add_command_listener(self._aka_command, self.parse_aka_command, strip_preamble=True,
            direct_reply=True)
        
        bot.add_event_listener('on_message', self.parse_other_commands)
    
    def _register_commands_from_registry(self, registry):
        for user in registry:
            for command in registry[user]:
                self._bot.register_command(self, command)
    
    def _load_registry(self, filename):
        with self._registry_mutex:
            try:
                infile = open(filename, 'r')
                data = json.load(infile)
                infile.close()
                
                return data
            except Exception as e:
                self.error('Error loading AKA registry: {}'.format(str(e)))
                return None
    
    def _save_registry(self, filename):
        with self._registry_mutex:
            try:
                outfile = open(filename, 'w+')
                data = json.dump(self._registry, fp=outfile)
                outfile.close()
                self.log('Saved AKA registry: {}'.format(filename))
            except Exception as e:
                self.error('Error saving AKA registry: {}'.format(str(e)))
    
    def has_command(self, command):
        with self._registry_mutex:
            for user in self._registry:
                if command in self._registry[user]:
                    return True
            
            return False
    
    def add_entry(self, command, target, user='global'):
        with self._registry_mutex:
            if not user in self._registry:
                self._registry[user] = dict()
            
            self._bot.register_command(self, command)
            self._registry[user][command] = target
        
        self._save_registry(self._registry_filename)
    
    def get_entry(self, command, user='global'):
        with self._registry_mutex:
            if not user in self._registry or not command in self._registry[user]:
                return None
            
            return self._registry[user][command]
    
    def remove_entry(self, command, user='global'):
        with self._registry_mutex:
            if not user in self._registry or not command in self._registry[user]:
                return False
            
            del self._registry[user][command]
        
        if not self.has_command(command):
            self._bot.unregister_command(self, command)
        
        self._save_registry(self._registry_filename)
        return True
    
    def parse_aka_command(self, message):
        # TODO: fix argparser so this hack isn't necessary
        if message.get_text() == '--list':
            with self._registry_mutex:
                output = list()
                
                for key in self._registry:
                    output.append(str(key) + ':')
                    
                    for command in self._registry[key]:
                        output.append('    {}{} -> {}{}'.format(
                            self._env_command_prefix, command,
                            self._env_command_prefix, self._registry[key][command]))
                    
                    output.append('')
            
            return self._bot.post('\n'.join(output))
        
        self._argparser.reset_error()
        args = self._argparser.parse_args(shlex.split(message.get_text(), posix=False))
        
        if self._argparser.has_error() or args.help:
            buffer = io.StringIO()
            self._argparser.print_help(buffer)
            buffer.seek(0)
            return buffer.read()
        
        username = 'u' + str(message.get_alias())
        target = ' '.join(args.target)
        
        if not args.alias.startswith(self._env_command_prefix):
            return 'A leading command prefix symbol ({}) is required in the alias'.format(self._env_command_prefix)
        else:
            args.alias = args.alias[len(self._env_command_prefix):]
        
        if len(args.target) > 0:
            if not target.startswith(self._env_command_prefix):
                return 'A leading command prefix symbol ({}) is required in the target'.format(self._env_command_prefix)
            else:
                target = target[len(self._env_command_prefix):]
        
        if args.local and vars(args).get('global'):
            return 'Conflicting options!'
        
        if args.delete:
            entry = self.get_entry(args.alias, username if args.local else 'global')
            
            if not entry:
                return 'No such {} entry "{}{}"'.format('user-local' if args.local else 'global',
                    self._env_command_prefix, args.alias)
            
            if not args.local and not vars(args).get('global'):
                return 'Must specify (-g, --global) or (-l, --local)'
            
            success = self.remove_entry(args.alias, username if args.local else 'global')
            
            if success:
                return 'Entry deleted'
            else:
                return 'Entry could not be deleted'
        elif len(args.target) == 0:
            entry = None
            local = True
            
            if not args.local and not vars(args).get('global'):
                entry = self.get_entry(args.alias, username)
                
                if not entry:
                    local = False
                    entry = self.get_entry(args.alias)
            elif args.local:
                entry = self.get_entry(args.alias, username)
            elif vars(args).get('global'):
                local = False
                entry = self.get_entry(args.alias)
            
            if not entry:
                return 'No such entry "{}{}"'.format(self._env_command_prefix, args.alias)
            else:
                return '({}) {}{} -> {}{}'.format('user-local' if local else 'global',
                    self._env_command_prefix, args.alias,
                    self._env_command_prefix, entry)
        else:
            allcommands = self._bot.get_commands()
            if message.is_internal():
                return RuntimeError("Can't create commands through internal commands.")
            
            if args.alias in [x for x in allcommands if allcommands[x]['owner'] != self]:
                return 'Command already exists'
            
            if args.local:
                self.add_entry(args.alias, target, username)
                return 'Added (user-local): {}{} -> {}{}'.format(
                    self._env_command_prefix, args.alias,
                    self._env_command_prefix, target)
            else:
                self.add_entry(args.alias, target)
                return 'Added (global): {}{} -> {}{}'.format(
                    self._env_command_prefix, args.alias,
                    self._env_command_prefix, target)
    
    def _resolve(self, message, prev=None, depth=0, maxdepth=10):
        if depth > maxdepth:
            self.error('Resolve recursion limit exceeded')
            return None
        
        text = message.get_text().strip()
        
        try:
            text = shlex.split(text)
        except:
            text = text.split(" ")
        
        entry = self.get_entry(text[0], 'u' + str(message.get_alias()))
        
        if not entry:
            entry = self.get_entry(text[0])
        
        if not entry:
            return prev
        
        payload = list()
        payload.append(entry)
        
        if len(text) > 1:
            if re.search(r'\$@', payload[0]):
                payload[0] = payload[0].replace('$@', " ".join(text[1:]))
                text = []
            elif re.search(r'\$\d', payload[0]):
                done = list()
                
                for n in range(1, len(text)):
                    if '${}'.format(n) in payload[0]:
                        payload[0] = payload[0].replace('${}'.format(n), text[n])
                        done.append(n)
                
                for n in done[::-1]:
                    del text[n]
            
            if len(text) > 1:
                payload += text[1:]
        
        currentmsg = JanteMessage(' '.join(payload), sender=message.get_sender())
        currentmsg.set_alias(message.get_alias())
        
        return self._resolve(currentmsg, prev=currentmsg, depth=depth + 1)
    
    def parse_other_commands(self, message):
        if not message.get_text().startswith(self._env_command_prefix):
            return
        
        message.set_text(message.get_text()[len(self._env_command_prefix):])
        result = self._resolve(message)
        
        if not result:
            return
        
        response = message.respond(self._env_command_prefix + result.get_text(), sender=result.get_sender())
        response.set_alias(result.get_alias())
        
        self._bot.fire_event('on_message', message=response)
