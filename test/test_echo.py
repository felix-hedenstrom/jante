import util.base_test

class TestBot(util.base_test.BaseTest):
    def test_base(self):
        self.assertEqual(self.eval("!echo test"), "test")

