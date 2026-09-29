# -----------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for
# license information.
# -----------------------------------------------------------------------------

from importlib import import_module
import os
import unittest
from unittest.mock import patch

from knack.util import CommandResultItem

from azdev.operations.pypi import _check_readme_render


class TestPackageHistoryValidation(unittest.TestCase):

    @patch('azdev.operations.pypi._check_history_headings', return_value=[])
    @patch('azdev.operations.pypi.cmd')
    @patch('azdev.operations.pypi.get_package_config')
    def test_legacy_package_keeps_setup_py_check(
            self, get_package_config_mock, cmd_mock, check_history_mock):
        package_dir = os.path.join('repo', 'src', 'legacy')
        get_package_config_mock.return_value = os.path.join(package_dir, 'setup.py')
        cmd_mock.return_value = CommandResultItem('', exit_code=0, error=None)

        self.assertEqual([], _check_readme_render(package_dir))

        self.assertTrue(cmd_mock.call_args.args[0].endswith(' setup.py check -r -s'))
        check_history_mock.assert_called_once_with(package_dir)

    @patch('azdev.operations.pypi._check_history_headings', return_value=[])
    @patch('azdev.operations.pypi._get_built_package_metadata')
    @patch('azdev.operations.pypi.get_package_config')
    def test_pyproject_package_uses_built_metadata(
            self, get_package_config_mock, get_metadata_mock, check_history_mock):
        package_dir = os.path.join('repo', 'src', 'modern')
        get_package_config_mock.return_value = os.path.join(package_dir, 'pyproject.toml')
        get_metadata_mock.return_value = {
            'description': None,
            'description_content_type': None,
            'version': '2.3.4',
        }

        self.assertEqual([], _check_readme_render(package_dir))

        check_history_mock.assert_called_once_with(package_dir, actual_version='2.3.4')


class TestPublishingDependency(unittest.TestCase):
    def test_declared_dependency_provides_publishing_api(self):
        # Do not mock this import: the resolved package must supply the API used
        # by publish_extensions, even when installed from a built azdev wheel.
        module = import_module('azure.multiapi.storage.v2018_11_09.blob')
        self.assertTrue(callable(module.BlockBlobService))


if __name__ == '__main__':
    unittest.main()
