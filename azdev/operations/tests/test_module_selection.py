# -----------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for
# license information.
# -----------------------------------------------------------------------------

import sys
import types
import unittest
from unittest.mock import Mock, patch

from azdev.operations import command_change, statistics


class TestModuleSelection(unittest.TestCase):

    def test_selection_before_git_filter(self):
        operations = (
            (command_change, 'export_command_meta'),
            (statistics, 'list_command_table'),
        )
        selections = (
            (None, None, ('core', 'mod', 'ext')),
            ([], [], ('core', 'mod', 'ext')),
            (['CLI'], None, ('core', 'mod')),
            (['EXT'], None, ('ext',)),
            (['monitor', 'ssh'], ['monitor', 'ssh'], ('core', 'mod', 'ext')),
        )
        for operation, function_name in operations:
            for modules, include_only, retained in selections:
                for include_whl_extensions in (False, True):
                    with self.subTest(operation=function_name, modules=modules,
                                      include_whl_extensions=include_whl_extensions):
                        self._check_selection(operation, function_name, modules, include_only,
                                              retained, include_whl_extensions)

    def _check_selection(self, operation, function_name, modules, include_only,
                         retained, include_whl_extensions):
        table = {
            'core': {'azure-cli-core': 'repo/src/azure-cli-core'},
            'mod': {'monitor': 'repo/src/azure-cli/azure/cli/command_modules/monitor'},
            'ext': {'azext_ssh': 'extensions/src/ssh'},
        }
        expected = {key: value.copy() if key in retained else {} for key, value in table.items()}
        cli_modules = {name: types.ModuleType(name) for name in ('azure', 'azure.cli', 'azure.cli.core')}
        cli_modules['azure.cli.core'].get_default_cli = Mock()
        # Stop at the Git filter so this tests selection without loading real CLI commands.
        with patch.dict(sys.modules, cli_modules), \
                patch.object(operation, 'require_azure_cli'), \
                patch.object(operation, 'heading'), \
                patch('azdev.utilities.path.get_path_table', return_value=table) as get_paths, \
                patch.object(operation, 'filter_by_git_diff',
                             side_effect=RuntimeError('selection complete')) as git_filter:
            with self.assertRaisesRegex(RuntimeError, 'selection complete'):
                getattr(operation, function_name)(
                    modules=modules, git_source='feature', git_target='dev', git_repo='repo',
                    include_whl_extensions=include_whl_extensions)

        get_paths.assert_called_once_with(include_only=include_only,
                                          include_whl_extensions=include_whl_extensions)
        git_filter.assert_called_once_with(expected, 'feature', 'dev', 'repo')
        cli_modules['azure.cli.core'].get_default_cli.assert_not_called()
