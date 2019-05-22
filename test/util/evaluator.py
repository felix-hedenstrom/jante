"""
@Author Felix Hedenström
Creates a wrapper around the bot class that allows the user to test commands by talking directly to the bot.
"""

import sys
import configparser
import threading

sys.path.append("..")

import bot

class Evaluator:
    def __init__(self):
         
        
        config = configparser.ConfigParser()
        config.read('test-settings.ini')
        
        self._bot = bot.Bot(None,config, testing=True)
        # TODO should create a temporary storage folder which it then deletes
        
        threading.Thread(target=self._bot.start).start()

    def eval(self, text):
        return self._bot.evaluate(text, timeout=5)
    
    def shutdown(self):
        self._bot._shutdown()
