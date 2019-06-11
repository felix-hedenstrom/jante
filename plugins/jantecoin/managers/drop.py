import time

import random

import threading

from libs.jantemessage import JanteMessage 

class CoinDrop:
    def __init__(self, config, parent):
        self._config = config
        self._parent = parent
        
        self._mutex = threading.Lock()
        
        self._min_time = self._config.getfloat("drop", "drop_min_time")
        self._max_time = self._config.getfloat("drop", "drop_max_time")
        self._award = self._config.getfloat("drop", "drop_award")
        self._event_active = False
        
        if not self._min_time <= self._max_time:
            raise ValueError("Min time must be lower than max time.")
        
        self._next_drop = self.next_drop()
        
    def next_drop(self):
        return time.time() + random.uniform(3600 * self._min_time, 3600 * self._max_time)
        
    def calc_prob(self):
        x = float(time.time() - self._last_drop - 3600 * self._min_time) / (3600 * self._max_time)
        return float(pow(self._help_factor, x) - 1) / (self._help_factor - 1)
    
    def maybe_drop_currency(self, timeval):
        with self._mutex:
            #print(self.calc_prob())
            if self._event_active or time.time() < self._next_drop:
                return
        
            self._event_active = True
            
            for channel in self._parent.getChannels():
                self._parent._bot.addMessage(jantemessage("Some {} just dropped!".format(self._config["currency"]["full_name"]), address=channel))
            
            return
            
    def award(self):
        return self._award
        
    def grab(self):
        with self._mutex:
            if self._event_active:
                self._event_active = False
                self._next_drop = self.next_drop()
                return True
            else:
                return False
