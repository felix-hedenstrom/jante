"""
@Author Felix Hedenström
"""

from .evaluator import Evaluator 
import unittest

class BaseTest(unittest.TestCase):
    def setUp(self):
        self.__evaluator = Evaluator()
    def __init__(self, tests=()):
        super().__init__(tests)
    def eval(self, text):
        return self.__evaluator.eval(text)
    def tearDown(self):
        self.__evaluator.shutdown()
