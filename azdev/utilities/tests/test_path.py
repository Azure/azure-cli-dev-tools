# -----------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for
# license information.
# -----------------------------------------------------------------------------


import importlib.util
import sys
import types
import unittest
import os
import shutil
import tempfile
from unittest.mock import patch

from azdev.utilities import get_name_index, get_path_table


def _azure_cli_installed():
    try:
        return importlib.util.find_spec('azure.cli.core.extension') is not None
    except (ImportError, ValueError):
        return False


def _stub_azure_cli_extension(extensions_dir):
    """Provide a minimal `azure.cli.core.extension` so path discovery can be unit tested.

    `get_path_table` and `get_name_index` import `EXTENSIONS_DIR` to locate wheel
    installed extensions, which otherwise requires a full azure-cli installation.
    """
    modules = {name: types.ModuleType(name)
               for name in ('azure', 'azure.cli', 'azure.cli.core', 'azure.cli.core.extension')}
    modules['azure.cli.core.extension'].EXTENSIONS_DIR = extensions_dir
    return patch.dict(sys.modules, modules)


@unittest.skipUnless(_azure_cli_installed(), 'azure-cli is not installed. Run `azdev setup` first.')
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


class TestCorePackageDiscovery(unittest.TestCase):

    def setUp(self):
        self.cli_repo = tempfile.mkdtemp()
        self.addCleanup(shutil.rmtree, self.cli_repo)
        self.src_dir = os.path.join(self.cli_repo, 'src')
        os.makedirs(self.src_dir)
        self.extensions_dir = os.path.join(self.cli_repo, 'extensions')
        os.makedirs(self.extensions_dir)
        azure_cli_stub = _stub_azure_cli_extension(self.extensions_dir)
        azure_cli_stub.start()
        self.addCleanup(azure_cli_stub.stop)

    def _write(self, relative_path, content=''):
        path = os.path.join(self.cli_repo, relative_path)
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, 'w', encoding='utf-8') as stream:
            stream.write(content)

    @patch('azdev.utilities.path.get_ext_repo_paths', return_value=[])
    @patch('azdev.utilities.path.get_cli_repo_path')
    def test_core_tables_support_both_package_formats(self, get_cli_repo_path_mock, _):
        get_cli_repo_path_mock.return_value = self.cli_repo
        self._write('src/legacy/setup.py', 'from setuptools import setup\n')
        self._write(
            'src/modern/pyproject.toml',
            '[build-system]\nrequires = ["setuptools"]\n',
        )
        self._write('src/tool-only/pyproject.toml', '[tool.ruff]\ntarget-version = "py310"\n')
        self._write('src/tools/nested/pyproject.toml', '[project]\nname = "nested"\n')

        path_table = get_path_table()
        name_index = get_name_index()

        self.assertEqual(
            {
                'legacy': os.path.join(self.src_dir, 'legacy'),
                'modern': os.path.join(self.src_dir, 'modern'),
            },
            path_table['core'],
        )
        self.assertEqual('azure-cli-legacy', name_index['legacy'])
        self.assertEqual('azure-cli-modern', name_index['modern'])
        self.assertNotIn('tool-only', path_table['core'])
        self.assertNotIn('tools', path_table['core'])


if __name__ == '__main__':
    unittest.main()
