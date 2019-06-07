import shlex
import threading
import argparse #TODO this should probably be included in janteparse


from datetime import datetime, timedelta

from plugins.parsingplugintemplate import ParsingPluginTemplate

from plugins.eval.syntaxhandlers.evaluator import Evaluator

import libs.janteparse as janteparse 

class EvalPlugin(ParsingPluginTemplate):
    """
    Evaluate expressions.

    Expressions should be formed as
        !eval x = !echo foo; !echo $x bar

    Variable assignments should end with ;
    Nested calls can be made
        !eval !roll $(!list --escape movies)
    Variables also have scope and works as normal scopes. Inner scopes can access variables from outer scopes but not the other way around.

    The value of variables is saved on decleration and reused.

    To create a function try using the !aka plugin
    """
    def __init__(self, bot):
        super().__init__(bot, command="eval", description="Evaluate statements!")
        self._id = 0
        self._mutex = threading.Lock()

        self._argparser = janteparse.JanteParser(description=self.__doc__, prog="eval", add_help=False, formatter_class=argparse.RawTextHelpFormatter)

        self._argparser.add_argument('-h', '--help', default=False, action='store_true', help="Show this help message")
        default_timeout = 5
        self._argparser.add_argument('-t', '--time-limit', type=int, default=default_timeout, help="Max amount of seconds that the expression will be evaluated under. Only integers are accepted. (Default: {})".format(default_timeout))
        self._argparser.add_argument('expression', nargs=argparse.REMAINDER, help="The expression that is to be evaluated.")


    def _generate_ID(self):
        with self._mutex:
            self._id += 1
            return ("evaluator", self._id)

    def parse(self, message):
        try:
            args = self._argparser.parse_args(message.get_text().split())

        except Exception as e:

            return janteparse.ArgumentParserError("\n{}".format(e)) #RuntimeError("Could not parse message. {}".format(self.parser.format_usage()))

        if args.help:
            return self._argparser.format_help()

        if not args.expression:
            return self._argparser.format_usage()

        text = " ".join(args.expression)
        e = Evaluator(message, self._generate_ID(), self._bot, datetime.now() + timedelta(seconds=args.time_limit), self._bot.get_command_prefix())

        text_response = e.evaluate(text)
        e.remove_listener()
        return text_response
