import util.base_test

class TestEcho(util.base_test.BaseTest):
    def test_base(self):
        self.assertIsInstance(self.eval("!thisisnotacommandimprettysure"), RuntimeError)
