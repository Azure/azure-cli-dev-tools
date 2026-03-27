# -----------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for
# license information.
# -----------------------------------------------------------------------------

import unittest
from unittest import mock
import os

from knack.util import CLIError, CommandResultItem

from azdev.operations.latest_index import generate_latest_index, verify_latest_index


class LatestIndexTestCase(unittest.TestCase):

    @mock.patch('azdev.operations.latest_index.py_cmd')
    @mock.patch('azdev.operations.latest_index.os.path.isfile', return_value=True)
    @mock.patch('azdev.operations.latest_index.os.path.isdir', return_value=True)
    def test_generate_with_explicit_repo_path(self, _, __, mock_py_cmd):
        mock_py_cmd.return_value = CommandResultItem('generated', exit_code=0, error=None)

        generate_latest_index(cli_path='/fake/azure-cli')

        self.assertTrue(mock_py_cmd.called)
        command = mock_py_cmd.call_args.args[0]
        self.assertIn('generate_latest_indices.py generate', command)
        self.assertEqual(os.path.abspath('/fake/azure-cli'), mock_py_cmd.call_args.kwargs['cwd'])
        self.assertFalse(mock_py_cmd.call_args.kwargs['is_module'])

    @mock.patch('azdev.operations.latest_index.py_cmd')
    @mock.patch('azdev.operations.latest_index.os.path.isfile', return_value=True)
    @mock.patch('azdev.operations.latest_index.os.path.isdir', return_value=True)
    @mock.patch('azdev.operations.latest_index.get_cli_repo_path', return_value='/configured/azure-cli')
    def test_verify_uses_configured_repo_path(self, _, __, ___, mock_py_cmd):
        mock_py_cmd.return_value = CommandResultItem('verified', exit_code=0, error=None)

        verify_latest_index()

        self.assertEqual('/configured/azure-cli', mock_py_cmd.call_args.kwargs['cwd'])

    @mock.patch('azdev.operations.latest_index.py_cmd')
    @mock.patch('azdev.operations.latest_index.os.path.isfile', return_value=True)
    @mock.patch('azdev.operations.latest_index.os.path.isdir', return_value=True)
    def test_verify_non_zero_exit_is_propagated(self, _, __, mock_py_cmd):
        # simulate bytes output as returned by py_cmd on failure
        mock_py_cmd.return_value = CommandResultItem(b'stale\r\n', exit_code=1, error='mismatch')

        with self.assertRaises(SystemExit) as ex:
            verify_latest_index(cli_path='/fake/azure-cli')

        self.assertEqual(1, ex.exception.code)

    def test_non_latest_profile_is_rejected(self):
        with self.assertRaises(CLIError):
            generate_latest_index(cli_path='/fake/azure-cli', profile='2019-03-01-hybrid')

    def test_all_profiles_flag_is_rejected(self):
        with self.assertRaises(CLIError):
            verify_latest_index(cli_path='/fake/azure-cli', all_profiles=True)

    @mock.patch('azdev.operations.latest_index.display')
    @mock.patch('azdev.operations.latest_index.py_cmd')
    @mock.patch('azdev.operations.latest_index.os.path.isfile', return_value=True)
    @mock.patch('azdev.operations.latest_index.os.path.isdir', return_value=True)
    def test_bytes_output_decoded_and_hint_replaced(self, _, __, mock_py_cmd, mock_display):
        raw = b'files are out of date\r\nRun:\r\n  python scripts/generate_latest_indices.py generate\r\n'
        mock_py_cmd.return_value = CommandResultItem(raw, exit_code=1, error='mismatch')

        with self.assertRaises(SystemExit):
            verify_latest_index(cli_path='/fake/azure-cli')

        displayed = mock_display.call_args.args[0]
        self.assertNotIn("b'", displayed)
        self.assertNotIn('\\r\\n', displayed)
        self.assertNotIn('python scripts/generate_latest_indices.py generate', displayed)
        self.assertIn('azdev latest-index generate', displayed)
