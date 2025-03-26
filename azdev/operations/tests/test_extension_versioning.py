# -----------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for
# license information.
# -----------------------------------------------------------------------------


import unittest
from unittest.mock import patch
import os
from azdev.operations.extensions import cal_next_version, VersionUpgradeMod
TEST_DIR = os.path.abspath(os.path.join(os.path.abspath(__file__), '..'))


class ExtensionVersioningTestCase(unittest.TestCase):

    def test_version_upgrade_major(self):
        # stable version update major
        version_test = cal_next_version(base_meta_file=os.path.join(TEST_DIR, "jsons", "az_monitor_meta_before.json"),
                                        diff_meta_file=os.path.join(TEST_DIR, "jsons", "az_monitor_meta_after.json"),
                                        current_version="3.11.0")
        self.assertEqual("4.0.0", version_test.get("version"), "Version cal error")
        self.assertEqual(True, version_test.get("is_stable"), "Version tag error")
        self.assertEqual(False, version_test.get("preview_tag", False), "Version tag error")

    def test_version_preview_to_stable(self):
        # stable version update major
        version_test = cal_next_version(base_meta_file=os.path.join(TEST_DIR, "jsons", "az_monitor_meta_before.json"),
                                        diff_meta_file=os.path.join(TEST_DIR, "jsons", "az_monitor_meta_after.json"),
                                        current_version="3.11.0b12", next_version_pre_tag="stable")
        self.assertEqual("3.11.0", version_test.get("version"), "Version cal error")
        self.assertEqual(True, version_test.get("is_stable"), "Version tag error")
        self.assertEqual(False, version_test.get("preview_tag", False), "Version tag error")

    def test_version_upgrade_major_was_preview(self):
        # preview version update major and add preview suffix
        version_test = cal_next_version(base_meta_file=os.path.join(TEST_DIR, "jsons", "az_monitor_meta_before.json"),
                                        diff_meta_file=os.path.join(TEST_DIR, "jsons", "az_monitor_meta_after.json"),
                                        current_version="3.11.0", is_preview=True)
        self.assertEqual("4.0.0b1", version_test.get("version"), "Version cal error")
        self.assertEqual(False, version_test.get("is_stable"), "Version tag error")
        self.assertEqual(False, version_test.get("preview_tag", False), "Version tag error")

    def test_version_upgrade_major_was_exp(self):
        # preview version update major and add preview suffix
        version_test = cal_next_version(base_meta_file=os.path.join(TEST_DIR, "jsons", "az_monitor_meta_before.json"),
                                        diff_meta_file=os.path.join(TEST_DIR, "jsons", "az_monitor_meta_after.json"),
                                        current_version="3.11.0", is_experimental=True)
        self.assertEqual("4.0.0b1", version_test.get("version"), "Version cal error")
        self.assertEqual(False, version_test.get("is_stable"), "Version tag error")
        self.assertEqual("add", version_test.get("preview_tag", False), "Version preview tag error")
        self.assertEqual("remove", version_test.get("exp_tag", False), "Version exp tag error")

    def test_version_upgrade_major_to_preview(self):
        # preview version update major and add preview suffix
        version_test = cal_next_version(base_meta_file=os.path.join(TEST_DIR, "jsons", "az_monitor_meta_before.json"),
                                        diff_meta_file=os.path.join(TEST_DIR, "jsons", "az_monitor_meta_after.json"),
                                        current_version="3.11.0", next_version_pre_tag="preview")
        self.assertEqual("4.0.0b1", version_test.get("version"), "Version cal error")
        self.assertEqual(False, version_test.get("is_stable"), "Version tag error")
        self.assertEqual("add", version_test.get("preview_tag", False), "Version tag error")

    def test_version_upgrade_to_normal_version(self):
        # preview version update major and add preview suffix
        version_test = cal_next_version(base_meta_file=os.path.join(TEST_DIR, "jsons", "az_monitor_meta_before.json"),
                                        diff_meta_file=os.path.join(TEST_DIR, "jsons", "az_monitor_meta_after.json"),
                                        current_version="0.11.0", is_preview=True)
        self.assertEqual("1.0.0b1", version_test.get("version"), "Version cal error")
        self.assertEqual(False, version_test.get("is_stable"), "Version tag error")
        self.assertEqual(False, version_test.get("preview_tag", False), "Version tag error")

    def test_version_upgrade_major_tagged_from_preview(self):
        # preview version update pre num but user tagged major
        version_test = cal_next_version(base_meta_file=os.path.join(TEST_DIR, "jsons", "az_monitor_meta_before.json"),
                                        diff_meta_file=os.path.join(TEST_DIR, "jsons", "az_monitor_meta_after.json"),
                                        current_version="3.11.0b7", next_version_segment_tag="major")
        self.assertEqual("4.0.0b1", version_test.get("version"), "Version cal error")
        self.assertEqual(False, version_test.get("is_stable"), "Version tag error")

    def test_version_upgrade_minor_tagged_from_preview(self):
        # preview version update pre num but user tagged minor
        version_test = cal_next_version(base_meta_file=os.path.join(TEST_DIR, "jsons", "az_monitor_meta_before.json"),
                                        diff_meta_file=os.path.join(TEST_DIR, "jsons", "az_monitor_meta_after.json"),
                                        current_version="3.11.0b7", next_version_segment_tag="minor")
        self.assertEqual("3.12.0b1", version_test.get("version"), "Version cal error")
        self.assertEqual(False, version_test.get("is_stable"), "Version tag error")

    def test_version_upgrade_patch_tagged_from_preview(self):
        # preview version update pre num but user tagged patch
        version_test = cal_next_version(base_meta_file=os.path.join(TEST_DIR, "jsons", "az_monitor_meta_before.json"),
                                        diff_meta_file=os.path.join(TEST_DIR, "jsons", "az_monitor_meta_after.json"),
                                        current_version="3.11.0b7", next_version_segment_tag="patch")
        self.assertEqual("3.11.1b1", version_test.get("version"), "Version cal error")
        self.assertEqual(False, version_test.get("is_stable"), "Version tag error")

    def test_version_upgrade_minor_tagged(self):
        # stable version update minor as user tagged
        version_test = cal_next_version(base_meta_file=os.path.join(TEST_DIR, "jsons", "az_monitor_meta_before.json"),
                                        diff_meta_file=os.path.join(TEST_DIR, "jsons", "az_monitor_meta_after.json"),
                                        current_version="3.11.0", next_version_segment_tag="minor")
        self.assertEqual("3.12.0", version_test.get("version"), "Version cal error")
        self.assertEqual(True, version_test.get("is_stable"), "Version tag error")

    def test_version_upgrade_patch_tagged(self):
        # stable version update patch as user tagged
        version_test = cal_next_version(base_meta_file=os.path.join(TEST_DIR, "jsons", "az_monitor_meta_before.json"),
                                        diff_meta_file=os.path.join(TEST_DIR, "jsons", "az_monitor_meta_after.json"),
                                        current_version="3.11.0", next_version_segment_tag="patch")
        self.assertEqual("3.11.1", version_test.get("version"), "Version cal error")

    def test_version_upgrade_pre_tagged(self):
        # preview version update major but user tagged pre
        version_test = cal_next_version(base_meta_file=os.path.join(TEST_DIR, "jsons", "az_monitor_meta_before.json"),
                                        diff_meta_file=os.path.join(TEST_DIR, "jsons", "az_monitor_meta_after.json"),
                                        current_version="3.11.0b7", next_version_segment_tag="pre")
        self.assertEqual("3.11.0b8", version_test.get("version"), "Version cal error")
        self.assertEqual(False, version_test.get("is_stable"), "Version tag error")

    def test_version_upgrade_pre_untagged(self):
        # preview version update major, no tag, follow no major update more than once from last stable version rule
        version_test = cal_next_version(base_meta_file=os.path.join(TEST_DIR, "jsons", "az_monitor_meta_before.json"),
                                        diff_meta_file=os.path.join(TEST_DIR, "jsons", "az_monitor_meta_after.json"),
                                        current_version="3.11.0b7")
        self.assertEqual("4.0.0b1", version_test.get("version"), "Version cal error")
        self.assertEqual(False, version_test.get("is_stable"), "Version tag error")

    def test_version_upgrade_patch(self):
        # stable version update patch as breaking change detects empty
        version_test = cal_next_version(base_meta_file=os.path.join(TEST_DIR, "jsons", "az_ams_meta_before.json"),
                                        diff_meta_file=os.path.join(TEST_DIR, "jsons", "az_ams_meta_after.json"),
                                        current_version="3.11.0")
        self.assertEqual("3.11.1", version_test.get("version"), "Version cal error")

    @patch.object(VersionUpgradeMod, 'find_max_version')
    def test_version_upgrade_preview_break(self, find_max_version):
        # preview version update while no stable version before or stable version already lower in major
        def config_last_stable_version(_):
            return False, -1

        find_max_version.side_effect = config_last_stable_version
        version_test = cal_next_version(base_meta_file=os.path.join(TEST_DIR, "jsons",
                                                                    "az_costmanagement_meta_before.json"),
                                        diff_meta_file=os.path.join(TEST_DIR, "jsons",
                                                                    "az_costmanagement_meta_after.json"),
                                        current_version="1.0.0b3")
        self.assertEqual("1.0.0b4", version_test.get("version"), "Version cal error")
        self.assertEqual(False, version_test.get("is_stable"), "Version tag error")
        self.assertEqual("add", version_test.get("preview_tag", False), "Version tag error")

    @patch.object(VersionUpgradeMod, 'find_max_version')
    def test_version_upgrade_pure_preview_pattern_to_preview(self, find_max_version):
        # preview version update while no stable version before or stable version already lower in major
        def config_last_stable_version(_):
            return False, -1

        find_max_version.side_effect = config_last_stable_version
        version_test = cal_next_version(base_meta_file=os.path.join(TEST_DIR, "jsons",
                                                                    "az_costmanagement_meta_before.json"),
                                        diff_meta_file=os.path.join(TEST_DIR, "jsons",
                                                                    "az_costmanagement_meta_after.json"),
                                        current_version="1.0.0", is_preview=True)
        self.assertEqual("1.0.1b1", version_test.get("version"), "Version cal error")
        self.assertEqual(False, version_test.get("is_stable"), "Version tag error")
        self.assertEqual(False, version_test.get("preview_tag", False), "Version tag error")

    @patch.object(VersionUpgradeMod, 'find_max_version')
    def test_version_upgrade_pure_preview_pattern_to_stable(self, find_max_version):
        # preview version update while no stable version before or stable version already lower in major
        def config_last_stable_version(_):
            return False, -1

        find_max_version.side_effect = config_last_stable_version
        version_test = cal_next_version(base_meta_file=os.path.join(TEST_DIR, "jsons",
                                                                    "az_costmanagement_meta_before.json"),
                                        diff_meta_file=os.path.join(TEST_DIR, "jsons",
                                                                    "az_costmanagement_meta_after.json"),
                                        current_version="1.0.4", is_preview=True, next_version_pre_tag="stable")
        self.assertEqual("1.1.0", version_test.get("version"), "Version cal error")
        self.assertEqual(True, version_test.get("is_stable"), "Version tag error")
        self.assertEqual("remove", version_test.get("preview_tag", False), "Version tag error")


    def test_version_upgrade_pure_exp_pattern_to_stable(self):
        version_test = cal_next_version(base_meta_file=os.path.join(TEST_DIR, "jsons",
                                                                    "az_costmanagement_meta_before.json"),
                                        diff_meta_file=os.path.join(TEST_DIR, "jsons",
                                                                    "az_costmanagement_meta_after.json"),
                                        current_version="1.0.4", is_experimental=True, next_version_pre_tag="stable")
        self.assertEqual("1.1.0", version_test.get("version"), "Version cal error")
        self.assertEqual(True, version_test.get("is_stable"), "Version tag error")
        self.assertEqual(False, version_test.get("preview_tag", False), "Version tag error")
        self.assertEqual("remove", version_test.get("exp_tag", False), "Version tag error")
