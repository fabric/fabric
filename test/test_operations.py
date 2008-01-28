import unittest

class TestRun(unittest.TestCase):
    def setUp(self):
        pass

def suite():
    suite = unittest.TestSuite()
    suite.addTest(TestRun())
