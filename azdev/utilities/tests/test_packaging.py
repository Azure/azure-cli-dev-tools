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

from azdev.utilities.packaging import (
    build_package_wheel, find_package_configs, find_package_configs_recursive, generate_egg_info,
    get_package_config)


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

    def test_find_package_configs_recursive_reaches_nested_packages(self):
        # Extension repos register the repo root, not the `src` folder, so discovery
        # has to reach packages that are not immediate children.
        nested_legacy = os.path.join(self.root, 'src', 'legacy-ext')
        os.makedirs(nested_legacy)
        with open(os.path.join(nested_legacy, 'setup.py'), 'w', encoding='utf-8') as stream:
            stream.write('from setuptools import setup\n')
        nested_modern = os.path.join(self.root, 'src', 'modern-ext')
        os.makedirs(nested_modern)
        with open(os.path.join(nested_modern, 'pyproject.toml'), 'w', encoding='utf-8') as stream:
            stream.write('[project]\nname = "modern-ext"\n')
        # A tool-only pyproject.toml is not a package and must not be discovered.
        self._make_package('tool-only', pyproject='[tool.ruff]\n')

        self.assertEqual(
            sorted([os.path.join(nested_legacy, 'setup.py'),
                    os.path.join(nested_modern, 'pyproject.toml')]),
            sorted(find_package_configs_recursive(self.root)),
        )

    def test_find_package_configs_recursive_skips_unreadable_pyproject(self):
        legacy_dir = self._make_package('legacy', setup_py='from setuptools import setup\n')
        self._make_package('broken', pyproject='[build-system\n')

        with self.assertLogs(level='WARNING') as logs:
            configs = find_package_configs_recursive(self.root)

        self.assertEqual([os.path.join(legacy_dir, 'setup.py')], configs)
        self.assertTrue(any('broken' in message for message in logs.output))

    def test_find_package_configs_recursive_ignores_missing_root(self):
        self.assertEqual([], find_package_configs_recursive(os.path.join(self.root, 'nope')))

    @patch('azdev.utilities.packaging.py_cmd')
    def test_generate_egg_info_uses_setup_py_when_present(self, py_cmd_mock):
        package_dir = self._make_package('legacy', setup_py='from setuptools import setup\n')

        generate_egg_info(package_dir)

        self.assertEqual('setup.py egg_info', py_cmd_mock.call_args.args[0])
        self.assertFalse(py_cmd_mock.call_args.kwargs['is_module'])
        self.assertEqual(package_dir, py_cmd_mock.call_args.kwargs['cwd'])

    @patch('azdev.utilities.packaging.py_cmd')
    def test_generate_egg_info_without_setup_py_calls_setup_inline(self, py_cmd_mock):
        package_dir = self._make_package('modern', pyproject='[project]\nname = "modern"\n')

        generate_egg_info(package_dir)

        command = py_cmd_mock.call_args.args[0]
        self.assertTrue(command.startswith('-c '))
        self.assertTrue(command.endswith(' egg_info'))
        self.assertIn('from setuptools import setup; setup()', command)
        self.assertFalse(py_cmd_mock.call_args.kwargs['is_module'])
        self.assertEqual(package_dir, py_cmd_mock.call_args.kwargs['cwd'])

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
        self.assertTrue(command.startswith('build --wheel --no-isolation --outdir '))
        self.assertNotIn('setup.py', command)

    @patch('azdev.utilities.packaging.py_cmd')
    def test_build_failure_logs_output_and_reraises(self, py_cmd_mock):
        """A failed build must surface the build log, not just the CalledProcessError.

        Regression test: the output lives on ``CommandResultItem.result``. Reading a
        non-existent ``.output`` attribute raised ``AttributeError`` and hid the real
        failure entirely.
        """
        package_dir = self._make_package('broken', setup_py='from setuptools import setup\n')
        output_dir = os.path.join(self.root, 'dist')
        error = RuntimeError('build exploded')
        py_cmd_mock.return_value = CommandResultItem(
            'error: could not find a version that satisfies setuptools>=99',
            exit_code=1, error=error)

        with self.assertLogs(level='ERROR') as logs:
            with self.assertRaises(RuntimeError):
                build_package_wheel(package_dir, output_dir)

        self.assertTrue(any('setuptools>=99' in message for message in logs.output))

    @patch('azdev.utilities.packaging.py_cmd')
    def test_build_failure_decodes_bytes_output(self, py_cmd_mock):
        package_dir = self._make_package('broken-bytes', setup_py='from setuptools import setup\n')
        output_dir = os.path.join(self.root, 'dist')
        py_cmd_mock.return_value = CommandResultItem(
            b'byte-encoded failure detail', exit_code=1, error=RuntimeError('boom'))

        with self.assertLogs(level='ERROR') as logs:
            with self.assertRaises(RuntimeError):
                build_package_wheel(package_dir, output_dir)

        self.assertTrue(any('byte-encoded failure detail' in message for message in logs.output))


if __name__ == '__main__':
    unittest.main()
