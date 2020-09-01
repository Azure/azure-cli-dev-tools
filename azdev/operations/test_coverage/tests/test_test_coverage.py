# -----------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for
# license information.
# -----------------------------------------------------------------------------

import unittest
import os

from azdev.operations.test_coverage import (load_exclusions,
                                            parse_test_commands,
                                            load_command_table_and_command_loader,
                                            simplify_command_table,
                                            update_command_table,
                                            calculate_command_coverage_rate)

TEST_DIR = os.path.abspath(os.path.join(os.path.abspath(__file__), '..'))

class TestTestCoverage(unittest.TestCase):
    def test_load_exclusions(self):
        valid_exclusion_path = os.path.join(TEST_DIR, 'data', 'exclusions.json')
        exclusion = load_exclusions(valid_exclusion_path)
        self.assertItemsEqual(["network vnet show","storage account show"], exclusion)

        invalid_exclusion_path = os.path.join(TEST_DIR, 'data', 'invalid_exclusions.json')
        exclusion = load_exclusions(invalid_exclusion_path)
        self.assertItemsEqual([], exclusion)
