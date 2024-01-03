# -----------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for
# license information.
# -----------------------------------------------------------------------------
# pylint: disable=line-too-long

import unittest
import os
from azure_cli_diff_tool import meta_diff, version_upgrade
from azure_cli_diff_tool.utils import get_command_tree, extract_cmd_name, extract_cmd_property, extract_para_info, \
    extract_subgroup_name


class MyTestCase(unittest.TestCase):

    def test_parse_cmd_tree(self):
        cmd_name = "monitor log-profiles create"
        ret = get_command_tree(cmd_name)
        self.assertTrue(ret["is_group"], "group parse failed")
        self.assertFalse(ret["sub_info"]["sub_info"]["is_group"], "group parse failed")
        self.assertTrue(ret["sub_info"]["sub_info"]["cmd_name"] == "monitor log-profiles create", "group parse failed")

    def test_diff_dict_key_parse(self):
        test_key = "root['sub_groups']['monitor']['sub_groups']['monitor private-link-scope']['sub_groups']" \
                   "['monitor private-link-scope scoped-resource']['commands']" \
                   "['monitor private-link-scope scoped-resource list']['parameters'][0]['options'][1]"
        has_cmd, cmd_name = extract_cmd_name(test_key)
        self.assertTrue(has_cmd, "cmd parse failed from diff dict key")
        self.assertEqual(cmd_name, "monitor private-link-scope scoped-resource list", "cmd name extract failed")
        has_cmd_key, cmd_key = extract_cmd_property(test_key, cmd_name)
        self.assertTrue(has_cmd_key, "cmd property parse failed from diff dict key")
        self.assertEqual(cmd_key, "parameters", "cmd property extract failed")
        para_res = extract_para_info(test_key)
        self.assertEqual(para_res[0], "0", "cmd parameter parse failed")

    def test_diff_dict_key_for_subgroups(self):
        test_key = "root['sub_groups']['monitor']['sub_groups']['monitor account']"
        has_cmd, _ = extract_cmd_name(test_key)
        self.assertFalse(has_cmd, "cmd parse error from diff dict key")
        has_subgroup, subgroup_name = extract_subgroup_name(test_key)
        self.assertTrue(has_subgroup, "sub group parse failed from diff dict key")
        self.assertEqual(subgroup_name, "monitor account", "sub group name extract failed")

    def test_diff_meta(self):
        if not os.path.exists("./jsons/az_monitor_meta_before.json") \
                or not os.path.exists("./jsons/az_monitor_meta_after.json"):
            return
        result = meta_diff(base_meta_file="./jsons/az_monitor_meta_before.json",
                           diff_meta_file="./jsons/az_monitor_meta_after.json",
                           output_type="text")
        target_message = [
            "please confirm cmd `monitor private-link-scope scoped-resource show` removed",
            "sub group `monitor private-link-scope private-endpoint-connection cust` removed",
            "cmd `monitor private-link-scope private-link-resource list` update parameter `scope_name`: added property `type=string`",
            "cmd `monitor private-link-scope private-link-resource list` update parameter `resource_group_name`: removed property `id_part=resource_group` | diff_level: 2"
        ]
        for mes in target_message:
            found = False
            for line in result:
                if line.find(mes) > -1:
                    found = True
                    break
            self.assertTrue(found, "target message not found")

        ignored_message = [
            "updated property `is_aaz` from `False` to `True`"
        ]
        for mes in ignored_message:
            ignored = True
            for line in result:
                if line.find(mes) > -1:
                    ignored = False
                    break
            self.assertTrue(ignored, "ignored message found")

    def test_diff_meta_whitelist(self):
        if not os.path.exists("./jsons/az_ams_meta_before.json") \
                or not os.path.exists("./jsons/az_ams_meta_after.json"):
            return
        result = meta_diff(base_meta_file="./jsons/az_ams_meta_before.json",
                           diff_meta_file="./jsons/az_ams_meta_after.json",
                           output_type="text")
        self.assertEqual(result, [], "returned change isn't empty")

    def test_version_upgrade_major(self):
        # stable version update major
        version_test = version_upgrade(base_meta_file="./jsons/az_monitor_meta_before.json",
                                       diff_meta_file="./jsons/az_monitor_meta_after.json",
                                       current_version="3.11.0")
        self.assertEqual("4.0.0", version_test.get("version"), "Version cal error")
        self.assertEqual(True, version_test.get("is_stable"), "Version tag error")
        self.assertEqual(False, version_test.get("has_preview_tag"), "Version tag error")

    def test_version_upgrade_major_was_preview(self):
        # preview version update major and add preview suffix
        version_test = version_upgrade(base_meta_file="./jsons/az_monitor_meta_before.json",
                                       diff_meta_file="./jsons/az_monitor_meta_after.json",
                                       current_version="3.11.0", is_preview=True)
        self.assertEqual("4.0.0b1", version_test.get("version"), "Version cal error")
        self.assertEqual(False, version_test.get("is_stable"), "Version tag error")
        self.assertEqual(True, version_test.get("has_preview_tag"), "Version tag error")

    def test_version_upgrade_major_was_exp(self):
        # preview version update major and add preview suffix
        version_test = version_upgrade(base_meta_file="./jsons/az_monitor_meta_before.json",
                                       diff_meta_file="./jsons/az_monitor_meta_after.json",
                                       current_version="3.11.0", is_experimental=True)
        self.assertEqual("4.0.0b1", version_test.get("version"), "Version cal error")
        self.assertEqual(False, version_test.get("is_stable"), "Version tag error")
        self.assertEqual(True, version_test.get("has_preview_tag"), "Version tag error")

    def test_version_upgrade_major_to_preview(self):
        # preview version update major and add preview suffix
        version_test = version_upgrade(base_meta_file="./jsons/az_monitor_meta_before.json",
                                       diff_meta_file="./jsons/az_monitor_meta_after.json",
                                       current_version="3.11.0", next_version_pre_tag="preview")
        self.assertEqual("4.0.0b1", version_test.get("version"), "Version cal error")
        self.assertEqual(False, version_test.get("is_stable"), "Version tag error")
        self.assertEqual(False, version_test.get("has_preview_tag"), "Version tag error")

    def test_version_upgrade_minor_tagged(self):
        # stable version update minor as user tagged
        version_test = version_upgrade(base_meta_file="./jsons/az_monitor_meta_before.json",
                                       diff_meta_file="./jsons/az_monitor_meta_after.json",
                                       current_version="3.11.0", next_version_segment_tag="minor")
        self.assertEqual("3.12.0", version_test.get("version"), "Version cal error")
        self.assertEqual(True, version_test.get("is_stable"), "Version tag error")

    def test_version_upgrade_patch_tagged(self):
        # stable version update patch as user tagged
        version_test = version_upgrade(base_meta_file="./jsons/az_monitor_meta_before.json",
                                       diff_meta_file="./jsons/az_monitor_meta_after.json",
                                       current_version="3.11.0", next_version_segment_tag="patch")
        self.assertEqual("3.11.1", version_test.get("version"), "Version cal error")

    def test_version_upgrade_patch(self):
        # stable version update patch as breaking change detects empty
        version_test = version_upgrade(base_meta_file="./jsons/az_ams_meta_before.json",
                                       diff_meta_file="./jsons/az_ams_meta_after.json",
                                       current_version="3.11.0")
        self.assertEqual("3.11.1", version_test.get("version"), "Version cal error")


if __name__ == '__main__':
    unittest.main()
