# -----------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for
# license information.
# -----------------------------------------------------------------------------

import shlex
import unittest
from unittest.mock import patch, MagicMock

from azdev.utilities import quote_arg


class TestQuoteArg(unittest.TestCase):
    """Regression coverage for GitHub issue #550: editable installs must survive
    paths containing spaces (e.g. OneDrive folders)."""

    def test_posix_quoting_roundtrips_through_shlex(self):
        path = '/home/user/Azure Powershell/src/ssh'
        with patch('azdev.utilities.IS_WINDOWS', False):
            quoted = quote_arg(path)
        # POSIX command runners split with shlex.split, so the quoted form must
        # round-trip back to the original single argument.
        self.assertEqual(shlex.split('install -e {}'.format(quoted)), ['install', '-e', path])

    def test_windows_quoting_wraps_spaces(self):
        path = r'C:\Users\me\Azure Powershell\src\ssh'
        with patch('azdev.utilities.IS_WINDOWS', True):
            quoted = quote_arg(path)
        # On Windows the string is passed verbatim to CreateProcess, which treats a
        # space-containing path as multiple arguments unless it is double-quoted.
        self.assertTrue(quoted.startswith('"') and quoted.endswith('"'))
        self.assertIn(path, quoted)

    def test_no_spaces_is_unchanged_on_posix(self):
        path = '/home/user/src/ssh'
        with patch('azdev.utilities.IS_WINDOWS', False):
            self.assertEqual(quote_arg(path), path)


class TestEditableInstallUsesQuotedPath(unittest.TestCase):

    @patch('azdev.operations.extensions._invalidate_command_index')
    @patch('azdev.operations.extensions.pip_cmd')
    @patch('azdev.operations.extensions.find_files',
           return_value=['/repo/Azure Powershell/src/my-ext/my_ext.egg-info'])
    @patch('azdev.operations.extensions.find_package_configs_recursive',
           return_value=['/repo/Azure Powershell/src/my-ext/setup.py'])
    @patch('azdev.operations.extensions.get_ext_repo_paths', return_value=['/repo'])
    def test_add_extension_quotes_whitespace_path(self, _mock_paths, _mock_configs, _mock_find, mock_pip,
                                                  _mock_invalidate):
        mock_pip.return_value = MagicMock(error=None)

        from azdev.operations.extensions import add_extension
        add_extension(['my-ext'])

        # The path interpolated into the pip command must be quoted, not bare.
        command = mock_pip.call_args[0][0]
        self.assertNotIn('install -e /repo/Azure Powershell/src/my-ext ', command)
        self.assertIn(quote_arg('/repo/Azure Powershell/src/my-ext'), command)


if __name__ == '__main__':
    unittest.main()
