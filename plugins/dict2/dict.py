"""
@Author Felix H
Ported to argparse on 2019-01-15
"""
import threading
import traceback
import shlex
import json
import re
import configparser

import time

from plugins.parsingplugintemplate import ParsingPluginTemplate
from libs.janteparse import JanteParser, ArgumentParserError
import libs.nlp.similar as similar
from collections import defaultdict

class DictPlugin2(ParsingPluginTemplate):
    class DictManager():
        def __init__(self, config, filename):
            self._config = config
            self._filename = filename
                
            self._options = defaultdict(list) 
            
            try:
                file_object  = open(self._filename, "r").read()

                if not len(file_object) == 0:
                    self._datadict = defaultdict(dict, json.loads(file_object)) 
                else    :
                    self._datadict = defaultdict(dict)
            except:
                self._datadict = defaultdict(dict) 

            self._mutex = threading.Lock()
        
        def save(self):
            with self._mutex:
                file_object = open(self._filename, 'w+')
                file_object.write(json.dumps(self._datadict))
                file_object.close()

        def keys(user=None, global_=True):
            if global_:
                user = None
            return self._datadict[user].keys()

        def items(user=None, global_=True):
            if global_:
                items_ = self._datadict[None].items()
            else:
                items_ = self._datadict[user].items()

            return sorted(items_, key=lambda x: x[0])
            
        def remove(self, key, user=None, global_=True):
            if global_:
                user = None

            if not key in self._datadict[user]:
                return False
            
            del self._datadict[user][key]
            return True
        def get(self, key, user=None, global_=True):
            if global_:
                user=None
            return self._datadict[user][key]


        def keys(self, user=None, global_=True):
            if global_:
                user = None
            return self._datadict[user].keys()

        def add_new_pair(self, key, value, force, global_=True, user=None):
            """
            Returns true if value was inserted, false if it was already present and force == False
            """
            user_insert, time_insert = user, time.time()
            if global_:
                location = None
            else:
                location = user
            
            if key in self._datadict[location]:
                if force:
                    user_insert = self._datadict[location][key]["user_insert"]
                    time_insert = self._datadict[location][key]["time_insert"]
                else:
                    return False

            with self._mutex:
                self._datadict[location][key] = {
                            "value": value,
                            "user_insert": user_insert,
                            "time_insert": time_insert,
                            "user_update": user,
                            "time_update": time.time()
                    }
            return True

        


    def __init__(self, bot):
        self._config = configparser.ConfigParser()
        self._config.read("plugins/dict2/settings.ini")
        
        super(DictPlugin2, self).__init__(bot, command=self._config.get('dict','command', fallback="dict"), description="Keys and values!")


        filename = "{datapath}{filename}".format(datapath=self._bot.get_base_data_path(), filename=self._config.get("dict",'savefilename', fallback="dict2plugindata.json"))
        
        self._dict_manager = DictPlugin2.DictManager(self._config, filename)

        self.parser = JanteParser(description='Keeps a dictionary of things.', prog='dict', add_help=False)
        self.parser.add_argument('-h', '--help', action='store_true', required=False, help="Shows this helpful message.")
        self.parser.add_argument('-k', '--key', help="The key to save the value with.")
        self.parser.add_argument('-v', '--value', help="The value to be stored.")
        self.parser.add_argument('-r', '--remove', help="Remove a key-value pair.")
        self.parser.add_argument('-l', '--list', action='store_true', help="List all key-value pairs.")
        self.parser.add_argument('--raw', action='store_true', help="Output data as raw as possible.")
        self.parser.add_argument('--size', action='store_true', help="Show the number of keys that are saved.")
        self.parser.add_argument('--keys', action="store_true", help="Return a list of all keys.")
        self.parser.add_argument('-p', '--pick', type=int, help="Pick option <index> from options recommended to you earlier.")
        self.parser.add_argument('--force', '-f', action='store_true', help="Force an overwrite if the key already exists.")
        self.parser.add_argument('--global', dest="global_", action="store_true", help="Store or retrieve globally stored values")
        self.parser.add_argument('--info', action="store_true", help="Show more info about when supplying a key.")
        self.parser.add_argument("ARGS", nargs="*", help="Positional arguments to dict.")

    def save(self):
        self._dict_manager.save()

    def paste(self, text, message):
        return self._bot.get_service("paste").paste(text, message)
    
    def add_new_pair(self, key, value, force=False, user=None, global_=True):
        if len(key) < int(self._config.get('dict','min_key_length',fallback=3)):
            return ValueError("Key length was shorter than the minimum key length {}.".format(self._config.get('dict','min_key_length',fallback=3)))
        if "\n" in key:
            return ValueError("Can't have a newline in the key.")

        if self._dict_manager.add_new_pair(key, value, force=force, user=user, global_=global_):
            return "Inserted keypair \"{key}: {value}\".".format(key=key,value=value)
        else:
            return ValueError('Key "{}" is already present in the dict. Use --force to overwrite it.'.format(key))
    
    def parse(self, message):
        try:
            args = self.parser.parse_args(shlex.split(message.get_text()))
        
        except ArgumentParserError as error:
            return ArgumentParserError("\n{}".format(error))
       
        user = message.get_alias()

        if args.help:
            return self.parser.format_help()
        
        if args.list:
            ans = ""
            for key, value in self._dict_manager.items():
                ans += "{}\n\t{}\n".format(key, value)
            if ans == "":
                return "No pairs are stored."
            return self.paste(ans, message)
        
        #if args.pick:
        #    if len(self._options) == 0:
        #        return RuntimeError('There are no options to pick at this moment.')
        #    if args.pick > len(self._options) or args.pick < 1:
        #        return RuntimeError('You can only pick numbers between 1 and {}.'.format(len(self._options)))
        #    return self.paste(self._datadict[self._options[args.pick - 1]], message)
        
        if args.remove:
            key = args.remove.strip()
            if self._dict_manager.remove(key, user=user, global_=args.global_):
                
                self.save()
                return 'Value associated with key "{}" was removed.'.format(key)
            else:
                return 'Could not remove the key. Are you sure it is present?'

        if args.keys:
            return self.paste("\n".join(sorted(self._dict_manager.keys(user=user, global_=args.global_))), message)

        if args.size:
            size = self._dict_manager.size()
            if args.raw:
                return str(size)
            return 'There are {} keys at the moment.'.format(sssssssssssssssssss)

        if (args.value or args.key):
            if not (args.value and args.key):
                return ValueError("Must supply both key and value")
            return self.add_new_pair(args.key, args.value, args.force, message)


        m = re.match(r"(.*[^\s]+)\s*:=\s*(.+)", " ".join(args.ARGS))
        if m:
            return self.add_new_pair(m.group(1), m.group(2), force=args.force, user=user, global_=args.global_)

        key = " ".join(args.ARGS)

        return self.get(key, extra_info=args.info, user=user, global_=args.global_)
        #with self._mutex:
        #    if not key in self._datadict:
        #        if len(self._datadict.keys()) == 0:
        #            return "There are currently no keys."
        #        self._options = similar.possibilities(key, list(self._datadict.keys()), use_random=True, subsets=True)
#
 #               if len(self._options) == 1:
  #                  return KeyError('\n"{}" is the only key similar to what you looked after. Here is its contents:\n{}'.format(self._options[0], self._datadict[self._options[0]]))
   #             tmp = []
    #            for i in range(1, len(self._options) + 1):
     #               tmp.append('{}: "{}"'.format(i, self._options[i - 1]))
#
 #               return KeyError('\nCould not find key "{}". Could you have meant:\n{}?'.format(key, '; '.join(tmp)))
  #          else:
   #             return self.paste(self._datadict[key], message)
