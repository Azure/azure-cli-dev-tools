# -----------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for
# license information.
# -----------------------------------------------------------------------------

import unittest
import os
from knack.util import CLIError

from azdev.operations.test_coverage import (load_exclusions,
                                            parse_test_commands,
                                            simplify_command_table,
                                            update_command_table,
                                            calculate_command_coverage_rate)

TEST_DIR = os.path.abspath(os.path.join(os.path.abspath(__file__), '..'))


class TestTestCoverage(unittest.TestCase):
    def test_load_exclusions(self):
        valid_exclusion_path = os.path.join(TEST_DIR, 'data', 'exclusions.json')
        exclusion = load_exclusions(valid_exclusion_path)
        self.assertCountEqual(["network vnet show", "storage account show"], exclusion)

        invalid_exclusion_path = os.path.join(TEST_DIR, 'data', 'invalid_exclusions.json')
        exclusion = load_exclusions(invalid_exclusion_path)
        self.assertCountEqual([], exclusion)

    def test_simplify_command_table(self):
        try:
            from azure.cli.core import get_default_cli
            from azure.cli.core.file_util import create_invoker_and_load_cmds_and_args
        except ImportError:
            raise CLIError("Azure CLI is not installed")

        az_cli = get_default_cli()

        create_invoker_and_load_cmds_and_args(az_cli)
        simplify_command_table(az_cli.invocation.commands_loader.command_table)
        az_cli.invocation.commands_loader.command_table = []
        simplify_command_table(az_cli.invocation.commands_loader.command_table)
        az_cli.invocation.commands_loader.command_table = None
        simplify_command_table(az_cli.invocation.commands_loader.command_table)

    def test_parse_test_commands(self):
        try:
            from azure.cli.core import get_default_cli
            from azure.cli.core.file_util import create_invoker_and_load_cmds_and_args
        except ImportError:
            raise CLIError("Azure CLI is not installed")

        az_cli = get_default_cli()

        create_invoker_and_load_cmds_and_args(az_cli)

        commands_record_file = [TEST_DIR, 'data', 'commands_record_file.txt']
        for ns in parse_test_commands(az_cli.invocation.parser, commands_record_file):
            pass

        commands_record_file = [TEST_DIR, 'data', 'invalid_commands_record_file.txt']
        for ns in parse_test_commands(az_cli.invocation.parser, commands_record_file):
            pass

    def test_update_command_table(self):
        try:
            from azure.cli.core import get_default_cli
            from azure.cli.core.file_util import create_invoker_and_load_cmds_and_args
        except ImportError:
            raise CLIError("Azure CLI is not installed")

        az_cli = get_default_cli()

        create_invoker_and_load_cmds_and_args(az_cli)

        commands_record_file = [TEST_DIR, 'data', 'commands_record_file.txt']

        simple_command = simplify_command_table(az_cli.invocation.commands_loader.command_table)
        for ns in parse_test_commands(az_cli.invocation.parser, commands_record_file):
            update_command_table(simple_command, ns)
