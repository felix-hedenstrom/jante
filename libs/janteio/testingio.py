from .basicio import BasicIO
import sys

class TestingIO(BasicIO):
    def __init__(self, bot):
        super().__init__(bot)
    def log(self, text):
        pass
    def error(self, text):
        sys.stderr.write(text)
