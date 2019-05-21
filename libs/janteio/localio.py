"""
@Author Felix Hedenström
"""
from abc import ABCMeta, abstractmethod

import sys
import os
import time

from .basicio import BasicIO

from ..jantemessage import JanteMessage

class LocalIO(BasicIO):

    def __init__(self, bot):
        super(LocalIO, self).__init__(bot)

    def send(self, message):
        with self._mutex:
            sys.stdout.write("\n")
            sys.stdout.write("------------------------------------\n")
            sys.stdout.write("Address: {}\n".format(message.get_address()))
            if not message.get_recipient() == "":
                sys.stdout.write("RECIPIENT:" + message.get_recipient() + "\n")
            if message.get_send_to_all():
                sys.stdout.write("SENDALL:" + str(message.get_send_to_all()) + "\n")
            sys.stdout.write("CHAT:\n" + message.get_text() + "\n")
            sys.stdout.write("------------------------------------\n")
            sys.stdout.write(">")

    def recieve(self):
        time.sleep(1)
        return JanteMessage(input(""), str(os.environ.get('USER')), "#Local", "#Local")

    def log(self, message):
        with self._mutex:
            sys.stdout.write("\n")
            sys.stderr.write("LOG:{}\n".format(message))
            sys.stderr.write(">")
