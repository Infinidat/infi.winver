
from infi import unittest
import mock

class InterfaceTestCase(unittest.TestCase):
    def setUp(self):
        from os import name
        if name != "nt":
            raise unittest.SkipTest

class WindowsTestCase(unittest.TestCase):
    pass
