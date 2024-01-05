# -----------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for
# license information.
# -----------------------------------------------------------------------------


import unittest
import os
from azdev.operations.command_change import export_command_meta, cmp_command_meta
from azdev.operations.extensions import version_upgrade
TEST_DIR = os.path.abspath(os.path.join(os.path.abspath(__file__), '..'))


class MyTestCase(unittest.TestCase):

    def test_version_upgrade_major(self):
        # stable version update major
        version_test = version_upgrade(base_meta_file=os.path.join(TEST_DIR, "jsons", "az_monitor_meta_before.json"),
                                       diff_meta_file=os.path.join(TEST_DIR, "jsons", "az_monitor_meta_after.json"),
                                       current_version="3.11.0")
        self.assertEqual("4.0.0", version_test.get("version"), "Version cal error")
        self.assertEqual(True, version_test.get("is_stable"), "Version tag error")
        self.assertEqual(False, version_test.get("has_preview_tag"), "Version tag error")

    def test_version_upgrade_major_was_preview(self):
        # preview version update major and add preview suffix
        version_test = version_upgrade(base_meta_file=os.path.join(TEST_DIR, "jsons", "az_monitor_meta_before.json"),
                                       diff_meta_file=os.path.join(TEST_DIR, "jsons", "az_monitor_meta_after.json"),
                                       current_version="3.11.0", is_preview=True)
        self.assertEqual("4.0.0b1", version_test.get("version"), "Version cal error")
        self.assertEqual(False, version_test.get("is_stable"), "Version tag error")
        self.assertEqual(True, version_test.get("has_preview_tag"), "Version tag error")

    def test_version_upgrade_major_was_exp(self):
        # preview version update major and add preview suffix
        version_test = version_upgrade(base_meta_file=os.path.join(TEST_DIR, "jsons", "az_monitor_meta_before.json"),
                                       diff_meta_file=os.path.join(TEST_DIR, "jsons", "az_monitor_meta_after.json"),
                                       current_version="3.11.0", is_experimental=True)
        self.assertEqual("4.0.0b1", version_test.get("version"), "Version cal error")
        self.assertEqual(False, version_test.get("is_stable"), "Version tag error")
        self.assertEqual(True, version_test.get("has_preview_tag"), "Version tag error")

    def test_version_upgrade_major_to_preview(self):
        # preview version update major and add preview suffix
        version_test = version_upgrade(base_meta_file=os.path.join(TEST_DIR, "jsons", "az_monitor_meta_before.json"),
                                       diff_meta_file=os.path.join(TEST_DIR, "jsons", "az_monitor_meta_after.json"),
                                       current_version="3.11.0", next_version_pre_tag="preview")
        self.assertEqual("4.0.0b1", version_test.get("version"), "Version cal error")
        self.assertEqual(False, version_test.get("is_stable"), "Version tag error")
        self.assertEqual(False, version_test.get("has_preview_tag"), "Version tag error")

    def test_version_upgrade_to_normal_version(self):
        # preview version update major and add preview suffix
        version_test = version_upgrade(base_meta_file=os.path.join(TEST_DIR, "jsons", "az_monitor_meta_before.json"),
                                       diff_meta_file=os.path.join(TEST_DIR, "jsons", "az_monitor_meta_after.json"),
                                       current_version="0.11.0", is_preview=True)
        self.assertEqual("1.0.0b1", version_test.get("version"), "Version cal error")
        self.assertEqual(False, version_test.get("is_stable"), "Version tag error")
        self.assertEqual(True, version_test.get("has_preview_tag"), "Version tag error")

    def test_version_upgrade_minor_tagged(self):
        # stable version update minor as user tagged
        version_test = version_upgrade(base_meta_file=os.path.join(TEST_DIR, "jsons", "az_monitor_meta_before.json"),
                                       diff_meta_file=os.path.join(TEST_DIR, "jsons", "az_monitor_meta_after.json"),
                                       current_version="3.11.0", next_version_segment_tag="minor")
        self.assertEqual("3.12.0", version_test.get("version"), "Version cal error")
        self.assertEqual(True, version_test.get("is_stable"), "Version tag error")

    def test_version_upgrade_patch_tagged(self):
        # stable version update patch as user tagged
        version_test = version_upgrade(base_meta_file=os.path.join(TEST_DIR, "jsons", "az_monitor_meta_before.json"),
                                       diff_meta_file=os.path.join(TEST_DIR, "jsons", "az_monitor_meta_after.json"),
                                       current_version="3.11.0", next_version_segment_tag="patch")
        self.assertEqual("3.11.1", version_test.get("version"), "Version cal error")

    def test_version_upgrade_patch(self):
        # stable version update patch as breaking change detects empty
        version_test = version_upgrade(base_meta_file=os.path.join(TEST_DIR, "jsons", "az_ams_meta_before.json"),
                                       diff_meta_file=os.path.join(TEST_DIR, "jsons", "az_ams_meta_after.json"),
                                       current_version="3.11.0")
        self.assertEqual("3.11.1", version_test.get("version"), "Version cal error")
