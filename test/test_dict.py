"""
@Author Felix Hedenström
"""

import util.base_test

class TestDict(util.base_test.BaseTest):
    def test_base(self):
        self.send_message("!dict test := answer")

        self.assertEqual(self.eval("!dict  test"), "answer")

    def test_overwrite(self):
        self.send_message("!dict test := answer")
        self.send_message("!dict -f test := other answer")

        self.assertEqual(self.eval("!dict test"), "other answer")
    
    def test_size(self):


        self.send_message("!dict a123 := 1")
        self.send_message("!dict b123 := 2")
        self.send_message("!dict c123 := 3")

        self.assertEqual(int(self.eval("!dict --raw --size")), 3)

        self.send_message("!dict d123 := 4")

        self.assertEqual(int(self.eval("!dict --raw --size")), 4)

    def test_picking(self):

        self.send_message("!dict abc := 0101")
        self.send_message("!dict abcd")


        # Should only have one availible option
        self.assertEqual(self.eval("!dict -p1"), "0101")
