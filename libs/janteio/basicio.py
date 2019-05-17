"""
@Author Felix Hedenström

Made PEP8 compliant on 2019-05-17
"""

from abc import ABCMeta, abstractmethod
import threading
import libs

import datetime
import sys

class BasicIO:
    def __init__(self, bot):
        self._bot = bot
        self._mutex = threading.Lock()
    # Sends a message to the recipient
    
    @abstractmethod
    def send(self, message):
        pass
    
    # Returns message, channel and sender in form (message, channel, sender).
    @abstractmethod
    def recieve(self):
        pass
        
    def log(self, text):
        text = str(text)
        timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M")#datetime.datetime.now().strftime('%H:%M')
        splittext = text.split("\n") 
        splittext = list(filter(None,splittext))
        ans = "{}\n".format(timestamp)
        #sys.stderr.write(str(splittext))
        for t in splittext:
            ans += "{}{}\n".format((len(timestamp) + 1) * " ", t)
        with self._mutex:
            sys.stderr.write(ans)
        sys.stderr.flush()

    def error(self, message):
        return self.log("ERROR:" + message)
    
    def exit(self, quitmessage):
        pass
