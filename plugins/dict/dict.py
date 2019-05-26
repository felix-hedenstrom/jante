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

from plugins.parsingplugintemplate import ParsingPluginTemplate
from libs.janteparse import JanteParser, ArgumentParserError
import libs.nlp.similar as similar

class DictPlugin(ParsingPluginTemplate):
    def __init__(self, bot):
        self._config = configparser.ConfigParser()
        self._config.read("plugins/dict/settings.ini")
        
        super(DictPlugin, self).__init__(bot, command=self._config['dict']['command'], description="Keys and values! Intended to be used for copypasta.")


        self._filename = "{datapath}{filename}".format(datapath=self._bot.get_base_data_path(), filename=self._config["dict"]['savefilename'])
        self._options = []

        try:
                file_object  = open(self._filename, "r").read()

                if not len(file_object) == 0:
                        self._datadict = json.loads(file_object)
                else:
                        self._datadict = {}
        except:
                self._datadict = {}

        self._mutex = threading.Lock()

        self.parser = JanteParser(description='Keeps a dictionary of things.', prog='dict', add_help=False)
        self.parser.add_argument('-h', '--help', action='store_true', required=False, help="Shows this helpful message.")
        self.parser.add_argument('-k', '--key', help="The key to save the value with.")
        self.parser.add_argument('-v', '--value', help="The value to be stored.")
        self.parser.add_argument('-r', '--remove', help="Remove a key-value pair.")
        self.parser.add_argument('-l', '--list', action='store_true', help="List all key-value pairs.")
        self.parser.add_argument('--size', action='store_true', help="Show the number of keys that are saved.")
        self.parser.add_argument('--keys', action="store_true", help="Return a list of all keys.")
        self.parser.add_argument('-p', '--pick', type=int, help="Pick option <index> from options recommended to you earlier.")
        self.parser.add_argument('--force', '-f', action='store_true', help="Force an overwrite if the key already exists.")
        self.parser.add_argument("ARGS", nargs="*", help="Positional arguments to dict.")

    def save(self):
        with self._mutex:
            file_object = open(self._filename, 'w')
            file_object.write(json.dumps(self._datadict))
            file_object.close()

    def paste(self, text, message):
        return self._bot.get_service("paste").paste(text, message)
    def add_new_pair(self, key, value, force, message):
        if len(key) < int(self._config['dict']['min_key_length']):
            return ValueError("Key length was shorter than the minimum key length {}.".format(self._config['dict']['min_key_length']))
        if "\n" in key:
            return ValueError("Can't have a newline in the key.")
        if key in self._datadict and not force:
            return ValueError('Key "{}" is already present in the dict. Use --force to overwrite it.'.format(key))
        with self._mutex:
            try:
                self._datadict[key] = value
            except:
                return RuntimeError("Something went wrong with pythons dictstructure.")
        self.save()
        return 'Added the keypair ("{}", "{}")'.format(key, self.paste(value, message))

    def parse(self, message):
        try:
            args = self.parser.parse_args(shlex.split(message.get_text()))
        except ArgumentParserError as error:
            return ArgumentParserError("\n{}".format(error))
        self.log("Args: {}".format(args.ARGS))
        if args.help:
            return self.parser.format_help()
        if args.list:
            ans = ""
            for key in self._datadict:
                ans += "{}\n\t{}\n".format(key, self._datadict[key])
            if ans == "":
                return "No pairs are stored."
            return self.paste(ans, message)
        if args.pick:
            if len(self._options) == 0:
                return RuntimeError('There are no options to pick at this moment.')
            if args.pick > len(self._options) or args.pick < 1:
                return RuntimeError('You can only pick numbers between 1 and {}.'.format(len(self._options)))
            return self.paste(self._datadict[self._options[args.pick - 1]], message)
        if args.remove:
            key = args.remove.strip()
            if not key in self._datadict:
                return KeyError("Key \"{}\" was not found in dict.".format(key))
            else:
                del self._datadict[key]
            self.save()
            return 'Value associated with key "{}" was removed.'.format(key)

        if args.keys:
            return self.paste("\n".join(sorted(self._datadict.keys())), message)

        if args.size:
            return 'There are {} keys at the moment.'.format(len(self._datadict))

        if (args.value or args.key):
            if not (args.value and args.key):
                return ValueError("Must supply both key and value")
            return self.add_new_pair(args.key, args.value, args.force, message)


        m = re.match(r"(.+[^\s]+)\s*:=\s*(.+)", " ".join(args.ARGS))
        if m:
            return self.add_new_pair(m.group(1), m.group(2), args.force, message)

        key = " ".join(args.ARGS)

        with self._mutex:
            if not key in self._datadict:
                if len(self._datadict.keys()) == 0:
                    return "There are currently no keys."
                self._options = similar.possibilities(key, list(self._datadict.keys()), use_random=True, subsets=True)

                if len(self._options) == 1:
                    return KeyError('\n"{}" is the only key similar to what you looked after. Here is its contents:\n{}'.format(self._options[0], self._datadict[self._options[0]]))
                tmp = []
                for i in range(1, len(self._options) + 1):
                    tmp.append('{}: "{}"'.format(i, self._options[i - 1]))

                return KeyError('\nCould not find key "{}". Could you have meant:\n{}?'.format(key, '; '.join(tmp)))
            else:
                return self.paste(self._datadict[key], message)
