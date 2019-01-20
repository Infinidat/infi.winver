import unittest
import os
from infi.winver import Windows


class TestWinver(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        if os.name != "nt":
            raise unittest.SkipTest("Windows only")

    def test_calls(self):
        windows = Windows()

        self.assertIsInstance(windows.is_windows_2000(), bool)
        self.assertIsInstance(windows.is_windows_xp(), bool)
        self.assertIsInstance(windows.is_windows_2003(), bool)
        self.assertIsInstance(windows.is_windows_2008(), bool)
        self.assertIsInstance(windows.is_windows_2008_r2(), bool)
        self.assertIsInstance(windows.is_windows_vista(), bool)
        self.assertIsInstance(windows.is_windows_7(), bool)
        self.assertIsInstance(windows.is_windows_8(), bool)
        self.assertIsInstance(windows.is_windows_10(), bool)
        self.assertIsInstance(windows.is_windows_2012(), bool)
        self.assertIsInstance(windows.is_windows_2012_r2(), bool)
        self.assertIsInstance(windows.is_windows_2016(), bool)
        self.assertIsInstance(windows.is_x86(), bool)
        self.assertIsInstance(windows.is_x64(), bool)
        self.assertIsInstance(windows.is_ia64(), bool)
        self.assertIsInstance(windows.is_server_core(), bool)
        self.assertIsInstance(windows.is_hyper_v(), bool)
        self.assertIsInstance(windows.is_cluster_aware(), bool)
        self.assertIsInstance(windows.greater_than("Windows Server 2008"), bool)
        self.assertIsInstance(windows.service_pack, int)
        self.assertIsInstance(windows.edition, str)
