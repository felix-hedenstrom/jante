"""
@Author Felix Hedenström
"""

from .evaluator import Evaluator 
import unittest
import subprocess
import configparser
class BaseTest(unittest.TestCase):
    def setUp(self):
        subprocess.check_call(['mkdir -p {}'.format(self._config.get('global', 'datapath'))], shell=True)
        self.__evaluator = Evaluator(self._config)
    def __init__(self, tests=()):
        super().__init__(tests)
        self._config = configparser.ConfigParser() 
        self._config.read('test-settings.ini')

    
    def eval(self, text, sender=None):
        return self.__evaluator.eval(text, sender=sender)
    
    def tearDown(self):
        self.__evaluator.shutdown()
        subprocess.check_call(['rm -rf {}'.format(self._config.get('global', 'datapath'))], shell=True)
    
    def send_message(self, m):
        self.__evaluator.send_message(m)

    def get_bot(self):
        return self.__evaluator.get_bot()
