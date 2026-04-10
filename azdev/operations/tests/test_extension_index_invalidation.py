# -----------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for
# license information.
# -----------------------------------------------------------------------------

import os
import tempfile
import unittest
from unittest.mock import patch

from azdev.operations.extensions import _invalidate_command_index, _COMMAND_INDEX_FILES


class TestInvalidateCommandIndex(unittest.TestCase):

    def test_deletes_all_index_files(self):
        """All four command index files should be deleted when they exist."""
        with tempfile.TemporaryDirectory() as tmpdir:
            for filename in _COMMAND_INDEX_FILES:
                filepath = os.path.join(tmpdir, filename)
                with open(filepath, 'w') as f:
                    f.write('{}')

            with patch('azdev.operations.extensions.get_azure_config_dir', return_value=tmpdir):
                _invalidate_command_index()

            for filename in _COMMAND_INDEX_FILES:
                self.assertFalse(os.path.exists(os.path.join(tmpdir, filename)),
                                 f'{filename} should have been deleted')

    def test_handles_missing_files_gracefully(self):
        """Should not raise when index files do not exist."""
        with tempfile.TemporaryDirectory() as tmpdir:
            with patch('azdev.operations.extensions.get_azure_config_dir', return_value=tmpdir):
                _invalidate_command_index()  # should not raise

    def test_handles_partial_files(self):
        """Should delete existing files and skip missing ones without error."""
        with tempfile.TemporaryDirectory() as tmpdir:
            existing = _COMMAND_INDEX_FILES[0]
            with open(os.path.join(tmpdir, existing), 'w') as f:
                f.write('{}')

            with patch('azdev.operations.extensions.get_azure_config_dir', return_value=tmpdir):
                _invalidate_command_index()

            self.assertFalse(os.path.exists(os.path.join(tmpdir, existing)))

    @patch('azdev.operations.extensions._invalidate_command_index')
    @patch('azdev.operations.extensions.pip_cmd')
    @patch('azdev.operations.extensions.find_files', return_value=['/repo/src/my-ext/setup.py'])
    @patch('azdev.operations.extensions.get_ext_repo_paths', return_value=['/repo'])
    def test_add_extension_calls_invalidate(self, _mock_paths, _mock_find, mock_pip, mock_invalidate):
        """add_extension should call _invalidate_command_index after installing."""
        from unittest.mock import MagicMock
        mock_pip.return_value = MagicMock(error=None)

        from azdev.operations.extensions import add_extension
        add_extension(['my-ext'])

        mock_invalidate.assert_called_once()

    @patch('azdev.operations.extensions._invalidate_command_index')
    @patch('azdev.operations.extensions.pip_cmd')
    @patch('azdev.operations.extensions.display')
    @patch('azdev.operations.extensions.find_files', return_value=['/repo/src/my-ext/my_ext.egg-info'])
    @patch('azdev.operations.extensions.get_ext_repo_paths', return_value=['/repo'])
    def test_remove_extension_calls_invalidate(self, _mock_paths, _mock_find, _mock_display,
                                                mock_pip, mock_invalidate):
        """remove_extension should call _invalidate_command_index after removing."""
        with patch('os.listdir', return_value=[]):
            from azdev.operations.extensions import remove_extension
            remove_extension(['my-ext'])

        mock_invalidate.assert_called_once()


if __name__ == '__main__':
    unittest.main()
