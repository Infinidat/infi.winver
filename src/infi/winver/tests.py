
from infi import unittest
import mock

EXAMPLES = [dict(
            OSVersionEx = '\x9c\x00\x00\x00\x06\x00\x00\x00\x01\x00\x00\x00\xb1\x1d\x00\x00\x02\x00\x00\x00Service Pack 1\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x01\x00\x00\x00\x12\x01\x03\x00',
            SystemInfo = '\t\x00\x00\x00\x00\x10\x00\x00\x00\x00\x01\x00\x00\x00\x00\x00\xff\xff\xfe\xff\xff\x07\x00\x00\x01\x00\x00\x00\x00\x00\x00\x00\x01\x00\x00\x00\xd8!\x00\x00\x00\x00\x01\x00\x06\x00\x02,',
            ProductInfo = 10L,),
           ]

class InterfaceTestCase(unittest.TestCase):
    def setUp(self):
        from os import name
        if name != "nt":
            raise unittest.SkipTest

    def test_print_script(self):
        from .scripts import print_records
        print_records()

from contextlib import contextmanager, nested
from . import Windows
class WindowsTestCase(unittest.TestCase):
   @contextmanager
   def _mocked_interface(self, record):
       with nested(mock.patch("infi.winver.interface.GetVersionExA"),
                   mock.patch("infi.winver.interface.GetSystemInfo"),
                   mock.patch("infi.winver.interface.GetProductInfo")) \
               as (GetVersionExA, GetSystemInfo, GetProductInfo):
           GetVersionExA.return_value = record["OSVersionEx"]
           GetSystemInfo.return_value = record["SystemInfo"]
           GetProductInfo.return_value = record["ProductInfo"]
           yield

   @unittest.parameters.iterate("record", EXAMPLES)
   def test_init(self, record):
       with self._mocked_interface(record):
           win = Windows()
