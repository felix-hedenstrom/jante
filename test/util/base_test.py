"""
@Author Felix Hedenström
"""

from .evaluator import Evaluator 
import unittest
import subprocess
import configparser
class BaseTest(unittest.TestCase):
    def setUp(self):
        self.__evaluator = Evaluator(self._config)
    def __init__(self, tests=()):
        super().__init__(tests)
        self._config = configparser.ConfigParser() 
        self._config.read('test-settings.ini')

        subprocess.check_call(['mkdir -p {}'.format(self._config.get('global', 'datapath'))], shell=True)
        subprocess.check_call(['rm -rf {}'.format(self._config.get('global', 'datapath'))], shell=True)
    
    def eval(self, text, sender=None):
        return self.__evaluator.eval(text, sender=sender)
    def tearDown(self):
        self.__evaluator.shutdown()
