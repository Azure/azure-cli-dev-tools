# -----------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for
# license information.
# -----------------------------------------------------------------------------


import unittest
import os
from azure_cli_diff_tool import meta_diff
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


if __name__ == '__main__':
    unittest.main()
