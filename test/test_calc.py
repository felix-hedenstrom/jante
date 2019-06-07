import util.base_test

class TestEcho(util.base_test.BaseTest):
    def test_base(self):
        self.assertEqual(self.eval("!calc --raw 1 + 1"), "2.0")
