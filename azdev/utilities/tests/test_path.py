import unittest
import os

from pprint import pprint
from azdev.utilities import get_path_table


class TestGetPathTable(unittest.TestCase):
    def setUp(self):
        self.path_table = get_path_table()

    def test_component(self):
        self.assertTrue('core' in self.path_table)
        self.assertTrue('ext' in self.path_table)
        self.assertTrue('mod' in self.path_table)

    def test_core_modules_directory_exist(self):
        if 'core' not in self.path_table:
            self.skipTest("No 'core' key in what get_path_table() return")

        core_modules = self.path_table['core']
        for _, mod_path in core_modules.items():
            self.assertTrue(os.path.isdir(mod_path))

    def test_command_modules_directory_exist(self):
        if 'mod' not in self.path_table:
            self.skipTest("No 'mod' key in what get_path_table() return")

        command_modules = self.path_table['mod']
        for _, mod_path in command_modules.items():
            self.assertTrue(os.path.isdir(mod_path))

    def test_extension_modules_directory_exist(self):
        if 'ext' not in self.path_table:
            self.skipTest("No 'ext' key in what get_path_table() return")

        if not self.path_table['ext']:
            self.skipTest("No extension modules installed by azdev")

        extension_moduels = self.path_table['ext']
        for _, mod_path in extension_moduels.items():
            self.assertTrue(os.path.isdir(mod_path))


if __name__ == '__main__':
    unittest.main()
