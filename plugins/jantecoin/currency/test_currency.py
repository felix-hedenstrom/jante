import unittest

import random

import jsonpickle

from jantecoin import JanteCoin #, JanteCoinFactory

class TestCurrency(unittest.TestCase):
    def test_str(self):
        self.assertEqual(str(JanteCoin(1,0, parts_in_whole=100)), "1")
        
        self.assertEqual(str(JanteCoin(1000, parts_in_whole=100)), "1000")
        self.assertEqual(str(JanteCoin(0, 1, parts_in_whole=1000)), "0.001")
        self.assertEqual(str(JanteCoin(1, 10, parts_in_whole=1000)), "1.01")
        
        
    def test_bad_inp(self):
        with self.assertRaises(ValueError):
            jc = JanteCoin(-1)
        with self.assertRaises(ValueError):
            jc = JanteCoin(1,1000)
            
    def test_equals(self):
        for i in range(0, 100):
            for j in range(0, 100):
                jc1 = JanteCoin(i, j)
                jc2 = JanteCoin(j, i)
                self.assertEqual(jc1 == jc2, i == j)
                self.assertEqual(jc1 != jc2, i != j)
    def test_lessthan(self):
        for i in range(0, 100):
            val1 = int(10 * random.random())
            val2 = int(10 * random.random())
            jc1 = JanteCoin(val1)
            jc2 = JanteCoin(val2)
            self.assertEqual(jc1 < jc2, val1 < val2)
        
    def test_addition(self):
        jc1 = JanteCoin(1, 90, parts_in_whole=100)
        jc2 = JanteCoin(2, 40, parts_in_whole=100)
        
        self.assertEqual(jc1 + jc2, JanteCoin(4, 30))
        
        self.assertEqual(JanteCoin(0, 90) + JanteCoin(0,90), JanteCoin(1, 80))
        
    def test_multiplication(self):
        max_number = 100
        factor = 5
        jc1 = JanteCoin(5, 21, parts_in_whole=100)
        
        
        
        self.assertEqual(factor * jc1, JanteCoin(26, 5))
        self.assertEqual(jc1 * factor, JanteCoin(26, 5))
        
        
        factor = 0.5
        self.assertEqual(factor * JanteCoin(5, 21), JanteCoin(2, 60))
        self.assertEqual(jc1 * factor, JanteCoin(2, 60))
        
        with self.assertRaises(TypeError):
            x = JanteCoin(10, 5) * JanteCoin(10, 5)
        
        factor = 1.5
        jc = JanteCoin(0, 80)
        self.assertEqual(jc * factor, JanteCoin(1,20))
        
    def test_multiplication_edge_cases(self):
        self.assertEqual(5 * JanteCoin(0, 20), JanteCoin(1))
        
        self.assertEqual(0.000001 * JanteCoin(0, 1), JanteCoin(0))
        
        self.assertEqual(1.5 * JanteCoin(1,2), JanteCoin(1, 53))
        
        self.assertEqual(JanteCoin(1,50) + JanteCoin(1) * 0.95, JanteCoin(2, 45))
        
        self.assertEqual(0.09095704204663863 * JanteCoin(1, parts_in_whole=10000), JanteCoin(0, 909, parts_in_whole=10000)) 
        
    def test_json(self):
        l = list()
        for j in range(10):
            for i in range(10, 10 + j):
                l.append(JanteCoin(i * j, i - j))
                
        self.assertListEqual(jsonpickle.decode(jsonpickle.encode(l)), l)
    
    def test_float_comparison(self):
        self.assertTrue(JanteCoin(0, 50) < 0.51)
        self.assertFalse(JanteCoin(1, 0) < 0.99)
        self.assertFalse(JanteCoin(0, 0) < 0.0)
        self.assertTrue(JanteCoin(0, 49) < 0.5)
        self.assertFalse(JanteCoin(0, 51) < 0.5)
        self.assertFalse(JanteCoin(1, 0) < -1)
    def test_bad_addition(self):
        with self.assertRaises(TypeError):
            JanteCoin(1,1) + 1.1
    def test_float_conversion(self):
        jc = JanteCoin(1,10)
        self.assertLess(1.09, jc.to_float())
        self.assertGreater(1.11, jc.to_float())
        self.assertAlmostEqual(jc.to_float(), 1.1)
        
        
    def test_subtraction(self):
        self.assertEqual(JanteCoin(1) - JanteCoin(1), JanteCoin(0))
        self.assertEqual(JanteCoin(1, 2) - JanteCoin(1, 2), JanteCoin(0))
        self.assertEqual(JanteCoin(1) - JanteCoin(0, 25), JanteCoin(0, 75))
        self.assertEqual(JanteCoin(10, 75) - JanteCoin(5, 90), JanteCoin(4, 85))
        
if __name__ == '__main__':
    unittest.main()