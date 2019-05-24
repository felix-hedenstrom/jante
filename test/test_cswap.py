import util.base_test

class TestCSwap(util.base_test.BaseTest):
    def test_same(self):
        self.assertEqual(self.eval("!cswap this is a test"), "this is a test")

    def test_cswap(self):
        self.assertEqual(self.eval("!cswap testing is good"), "gesting is tood")
   
        self.assertEqual(self.eval("!cswap dear old queen"), "qear old dueen")

    def test_spoon(self):
        self.assertEqual(self.eval("!cswap --spoon strong test"), "tong strest")
    
    def test_last(self):

        #TODO need a way to send a message without needing to wait for a response.
        pass
