"""
@Author Felix Hedenström
Creates a wrapper around the bot class that allows the user to test commands by talking directly to the bot.
"""

import sys
import configparser
from datetime import datetime, timedelta
import time
import threading

sys.path.append("..")

from libs.jantemessage import JanteMessage
import bot

class Evaluator:

    class EvaluatorInstance:
        def __init__(self, bot, id_, timeout=None):
            self._bot = bot
            self._message_mutex = threading.Lock()
            self._id = id_
            self._timeout = timeout

            def message_filter(message):
                return message.get_address() == self._id 
            self._message_filter = message_filter 
            self._bot.add_event_listener('on_message_sent', self.listener, prefilter=self._message_filter)
            self._messages = []
        
        def listener(self, message):
            with self._message_mutex:
                self._messages.append(message)

        def has_incoming_message(self):
            with self._message_mutex:
                return not len(self._messages) == 0 
        
        def evaluate_text(self, text):
            return self.evaluate(self._generate_message(text)) 

        def evaluate(self, m):
            self._bot.fire_event('on_message', message=m)
            timeout = datetime.now() + timedelta(seconds=self._timeout)
            
            while(not self.has_incoming_message() and datetime.now() < timeout):
                time.sleep(0.02)
            
            if not datetime.now() < timeout:
                return RuntimeError("Ran out of time on command {}.".format(m.get_text()))
         
            with self._message_mutex:
                inc_message = self._messages.pop()
                self._messages = []

            return inc_message
        
        def _generate_message(self, text):
            return JanteMessage(text, sender="testbot", address=self._id)
        
        def __del__(self):
            self._bot.remove_event_listener('on_message_sent', self.listener, prefilter=self._message_filter)


    def __init__(self):
         
        
        config = configparser.ConfigParser()
        config.read('test-settings.ini')
        self._id = 0
        self._bot = bot.Bot(None,config, testing=True)
         
        threading.Thread(target=self._bot.start).start()
   
    def eval(self, text, timeout=5, return_message=False):
        ei = Evaluator.EvaluatorInstance(self._bot, self.generate_id(), timeout=timeout)  
        m = ei.evaluate_text(text)
        del ei

        if return_message or type(m) != JanteMessage:
            return m
        else:
            return m.get_text()
    
    def shutdown(self):
        self._bot._shutdown()

    def generate_id(self):
        self._id += 1
        return ("testing", self._id)

