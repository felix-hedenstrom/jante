import util.base_test

class TestDict(util.base_test.BaseTest):
    def test_base(self):
        self.send_message("!dict test := answer")

        self.assertEqual(self.eval("!dict  test"), "answer")

    def test_overwrite(self):
        self.send_message("!dict test := answer")
        self.send_message("!dict test := other answer")

        self.assertEqual(self.eval("!dict test"), "other answer")
