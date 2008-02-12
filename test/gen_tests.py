#!/usr/bin/env python

'''
Generate .pyt files from the test_*.py templates.
'''

import glob

test_templates = glob.glob("test_*.py")

for template in test_templates:
    tfi = open(template, 'r')
    tfo = open(template+'t', 'w')
    tfo.write("""
import sys
import unittest
sys.path = ['','..'] + sys.path
import fabric

class TestCaseImpl(unittest.TestCase):
""")
    for line in tfi:
        tfo.write('    '+line)
    tfo.write("""

if __name__ == '__main__':
    try:
        unittest.main()
    except:
        exit(1)
    exit(0)
""")
    tfi.close()
    tfo.close()

alltests = open('alltests.pyt', 'w')
alltests.write('''
import imp
import unittest
import sys

test_modules = [
''')
for template in test_templates:
    name, _, _ = template.partition('.')
    alltests.write(
        '    imp.load_module("%s", open("test/%s.pyt","r"),"%s.pyt", (".pyt", "U", 1)),\n'
        % (name, name, name)
    )
alltests.write('''
]

names_of = unittest.defaultTestLoader.getTestCaseNames
tests = [m.TestCaseImpl for m in test_modules]
testcases = []
for cls in tests:
    for name in names_of(cls):
        testcases.append(cls(name))

suite = unittest.TestSuite()
suite.addTests(testcases)

runner = unittest.TextTestRunner()
runner.run(suite)
''')
alltests.close()

