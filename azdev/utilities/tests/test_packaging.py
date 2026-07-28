# -----------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for
# license information.
# -----------------------------------------------------------------------------

import os
import shutil
import tempfile
import unittest
from unittest.mock import patch

from knack.util import CLIError

from knack.util import CommandResultItem

from azdev.utilities.packaging import build_package_wheel, find_package_configs, get_package_config


class TestPackageConfig(unittest.TestCase):

    def setUp(self):
        self.root = tempfile.mkdtemp()
        self.addCleanup(shutil.rmtree, self.root)

    def _make_package(self, name, setup_py=None, pyproject=None):
        package_dir = os.path.join(self.root, name)
        os.makedirs(package_dir)
        if setup_py is not None:
            with open(os.path.join(package_dir, 'setup.py'), 'w', encoding='utf-8') as stream:
                stream.write(setup_py)
        if pyproject is not None:
            with open(os.path.join(package_dir, 'pyproject.toml'), 'w', encoding='utf-8') as stream:
                stream.write(pyproject)
        return package_dir

    def test_setup_py_package(self):
        package_dir = self._make_package('legacy', setup_py='from setuptools import setup\n')

        self.assertEqual(os.path.join(package_dir, 'setup.py'), get_package_config(package_dir))

    def test_pyproject_build_system_package(self):
        package_dir = self._make_package(
            'modern',
            pyproject='[build-system]\nrequires = ["setuptools"]\n',
        )

        self.assertEqual(os.path.join(package_dir, 'pyproject.toml'), get_package_config(package_dir))

    def test_pyproject_project_package(self):
        package_dir = self._make_package('pep621', pyproject='[project]\nname = "pep621"\n')

        self.assertEqual(os.path.join(package_dir, 'pyproject.toml'), get_package_config(package_dir))

    def test_tool_only_pyproject_is_ignored(self):
        package_dir = self._make_package('tool-only', pyproject='[tool.ruff]\ntarget-version = "py310"\n')

        self.assertIsNone(get_package_config(package_dir))

    def test_setup_py_takes_precedence_over_pyproject(self):
        package_dir = self._make_package(
            'transitioning',
            setup_py='from setuptools import setup\n',
            pyproject='this is not valid TOML',
        )

        self.assertEqual(os.path.join(package_dir, 'setup.py'), get_package_config(package_dir))

    def test_malformed_packaging_pyproject_reports_path(self):
        package_dir = self._make_package('malformed', pyproject='[build-system\n')

        with self.assertRaisesRegex(CLIError, r'malformed.*pyproject\.toml'):
            get_package_config(package_dir)

    def test_find_package_configs_is_immediate_and_deduplicated(self):
        legacy_dir = self._make_package(
            'legacy',
            setup_py='from setuptools import setup\n',
            pyproject='[tool.ruff]\n',
        )
        modern_dir = self._make_package(
            'modern',
            pyproject='[build-system]\nrequires = ["setuptools"]\n',
        )
        self._make_package('tool-only', pyproject='[tool.mypy]\nstrict = true\n')
        nested_dir = os.path.join(self.root, 'tools', 'nested-package')
        os.makedirs(nested_dir)
        with open(os.path.join(nested_dir, 'pyproject.toml'), 'w', encoding='utf-8') as stream:
            stream.write('[project]\nname = "nested"\n')

        self.assertEqual(
            [os.path.join(legacy_dir, 'setup.py'), os.path.join(modern_dir, 'pyproject.toml')],
            find_package_configs(self.root),
        )

    def test_find_package_configs_skips_unreadable_pyproject(self):
        legacy_dir = self._make_package('legacy', setup_py='from setuptools import setup\n')
        self._make_package('zz-broken', pyproject='[build-system\n')

        with self.assertLogs(level='WARNING') as logs:
            configs = find_package_configs(self.root)

        self.assertEqual([os.path.join(legacy_dir, 'setup.py')], configs)
        self.assertTrue(any('zz-broken' in message for message in logs.output))

    @patch('azdev.utilities.packaging.py_cmd')
    def test_build_legacy_package_preserves_setup_py_command(self, py_cmd_mock):
        package_dir = self._make_package('legacy', setup_py='from setuptools import setup\n')
        output_dir = os.path.join(self.root, 'dist')

        def _build(*_, **__):
            with open(os.path.join(output_dir, 'legacy-1.0.0-py3-none-any.whl'), 'wb'):
                pass
            return CommandResultItem('', exit_code=0, error=None)

        py_cmd_mock.side_effect = _build

        wheel_path = build_package_wheel(package_dir, output_dir)

        self.assertEqual(os.path.join(output_dir, 'legacy-1.0.0-py3-none-any.whl'), wheel_path)
        command = py_cmd_mock.call_args.args[0]
        self.assertTrue(command.startswith('setup.py bdist_wheel -d '))
        self.assertFalse(py_cmd_mock.call_args.kwargs['is_module'])

    @patch('azdev.utilities.packaging.py_cmd')
    def test_build_pyproject_package_uses_pep517_frontend(self, py_cmd_mock):
        package_dir = self._make_package('modern', pyproject='[project]\nname = "modern"\n')
        output_dir = os.path.join(self.root, 'dist')

        def _build(*_, **__):
            with open(os.path.join(output_dir, 'modern-1.0.0-py3-none-any.whl'), 'wb'):
                pass
            return CommandResultItem('', exit_code=0, error=None)

        py_cmd_mock.side_effect = _build

        build_package_wheel(package_dir, output_dir)

        command = py_cmd_mock.call_args.args[0]
        self.assertTrue(command.startswith('build --wheel --outdir '))
        self.assertNotIn('setup.py', command)


if __name__ == '__main__':
    unittest.main()
