import unittest

import seutil as se


class test_InspectAndReport(unittest.TestCase):

    def test_inspect_and_report(self):
        a = "Lorem ipsum dolor sit amet, consectetur adipiscing elit"
        for i in range(20):
            se.debug.inspect(a)
            se.debug.inspect(i)
            se.debug.inspect(a[i])

        se.debug.report()
