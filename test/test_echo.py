import util.base_test

class TestBot(util.base_test.BaseTest):
    def test_base(self):
        self.assertEqual(self.eval("!echo test"), "test")
    def test_capitalization(self):
        self.assertEqual(self.eval("!echo -c åäö abc"), "Åäö abc")
    def test_title(self):
        self.assertEqual(self.eval("!echo -t this is a test"), "This Is A Test")
    def test_upper(self):
        self.assertEqual(self.eval("!echo -u ÅÄÖ ABC"), "ÅÄÖ ABC")
    def test_encode(self):
        self.assertEqual(self.eval("!echo --url-encode \" \""), "%22+%22")
