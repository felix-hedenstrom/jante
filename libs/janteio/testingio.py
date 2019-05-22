from .basicio import BasicIO

class TestingIO(BasicIO):
    def __init__(self, bot):
        super().__init__(bot)
    def log(self, text):
        pass
