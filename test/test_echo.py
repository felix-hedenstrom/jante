import util.base_test

class TestBot(util.base_test.BaseTest):
    def test_base(self):
        self.assertEqual(self.eval("!echo test"), "test")
    def test_capitalization(self):
        self.assertEqual(self.eval("!echo -c åäö abc"), "Åäö abc")
        #self.assertEqual(self.eval("!echo -c ÅÄÖ"), "ÅÄÖ")

    def test_title(self):
        self.assertEqual(self.eval("!echo -t this is a test"), "This Is A Test")
