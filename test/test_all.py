import unittest

import test_operations

suites = [
    test_operations.suite(),
]

alltest = unittest.TestSuite(*suites)

runner = unittest.TextTestRunner()
runner.run(alltest)
