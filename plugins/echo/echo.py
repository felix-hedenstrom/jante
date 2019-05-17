"""
@Author Felix Hedenström
Loosely based on echo from bash
"""
from urllib.parse import urlencode 

from plugins.parsingplugintemplate import ParsingPluginTemplate
from libs.janteparse import JanteParser, ArgumentParserError 

class EchoPlugin(ParsingPluginTemplate):
    """
    Plugin for echoing things.
    Works similar to echo in bash.
    """
    def __init__(self, bot):
        super(EchoPlugin, self).__init__(bot,
                                         command="echo", description="Echo text back to the sender")

        self.parser = JanteParser(description='Echos things', prog='echo', add_help=False)
        self.parser.add_argument('-t', '--title', action='store_true', required=False,
                                 help="The first characters of each word will be made uppercase.")
        self.parser.add_argument('-l', '--lower', action='store_true', required=False,
                                 help="Changes all letters to lowercase.")
        self.parser.add_argument('-c', '--capitalize', action="store_true",
                                 help="Converts the first character of a string to uppercase.")
        self.parser.add_argument('-u', '--urlencode', action="store_true",
                                 help="Encodes the string according to URL-safe conventions")
        self.parser.add_argument('-h', '--help', action='store_true', required=False,
                                 help="Shows this helpful message.")
        self.parser.add_argument('--all-caps', '--upper', action='store_true', required=False,
                                 help="Return the string in all caps.")
        self.parser.add_argument("words", nargs="*",
                                 help="Words that will be echoed.")
    def parse(self, message):
        try:
            args = self.parser.parse_args(message.get_text().split(" "))
        except ArgumentParserError as error:
            return ArgumentParserError("\n{}".format(error))
        ans = " ".join(args.words)
        if args.help:
            return self.parser.format_help()
        if args.lower:
            ans = ans.lower()
        if args.title:
            ans = ans.title()
        if args.capitalize:
            ans = ans.capitalize()
        if args.all_caps:
            ans = ans.upper()
        if args.urlencode:
            ans = urlencode({"":ans})[1:]
        return ans
