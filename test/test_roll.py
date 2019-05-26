import util.base_test

class TestEcho(util.base_test.BaseTest):
    def test_default(self):
        for i in range(10):
            self.assertTrue(1 <= int(self.eval("!roll")) <= 6)

    
    def test_custom(self):
        for i in range(10):
            self.assertTrue(1 <= int(self.eval("!roll 10")) <= 10) 
 
    def test_word(self):

        self.assertTrue(self.eval("!roll test1 test2 test3") in ("test1", "test2", "test3"))
