"""
@Author Felix Hedenström
"""

from .localio import LocalIO
from .localcursesio import LocalCursesIO
from .testingio import TestingIO

import traceback
import sys

def missing_io(name):
    errormsg = traceback.format_exc()
    sys.stderr.write(errormsg)
    sys.stderr.write("Could not load {io}... Continuing since it is optional\n".format(io=name))
    

try:
    import janteio.ircio
except:
    missing_io("irc")

try:
    import janteio.xmpp.xmppio
except:
    missing_io("xmpp")
try:
    import janteio.discord.discordio
except:
    missing_io("discord")
    
class IOManager:
    """
    Wrapper for the different IO classes. Mainly to remove io imports and creation from bot.py
    """
    def __init__(self, type_, bot): 
        """
        type_ is a string describing the IO

        """
        self._bot = bot
        if type_ == "xmpp":
            self._io = janteio.xmpp.xmppio.XMPPIO(self._bot)
        elif type_ == "irc":
            self._io = janteio.ircio.IRCIO(self._bot)
        elif type_ == "old":
            self._io = LocalIO(self._bot)
        elif type_ == "local":
            self._io = LocalCursesIO(self._bot)
        elif type_ == "discord": 
            self._io = janteio.discord.discordio.discordIO(self._bot)
        elif type_ == "dummy":
            self._io = TestingIO(self._bot) 
        else:
            self._io = LocalCursesIO(self._bot)
    def log(self, text):
        self._io.log(text)
    def recieve(self):
        return self._io.recieve()
    def send(self, message):
        return self._io.send(message)
    def exit(self, message):
        return self._io.exit(message)
    def error(self, message):
        return self._io.error(message)
