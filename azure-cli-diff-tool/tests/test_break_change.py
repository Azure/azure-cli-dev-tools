# -----------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for
# license information.
# -----------------------------------------------------------------------------
# pylint: disable=line-too-long

import unittest
import os
from azure_cli_diff_tool import meta_diff
from azure_cli_diff_tool.utils import get_command_tree, extract_cmd_name, extract_cmd_property, extract_para_info, \
    extract_subgroup_name, extract_subgroup_deprecate_property, expand_deprecate_obj, extract_subgroup_property
TEST_DIR = os.path.abspath(os.path.join(os.path.abspath(__file__), '..'))


class CLIDiffToolTestCase(unittest.TestCase):

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

    def test_diff_dict_key_for_subgroups_deprecate_info(self):
        test_key = "root['sub_groups']['acr']['deprecate_info']['hide']"
        has_cmd, _ = extract_cmd_name(test_key)
        self.assertFalse(has_cmd, "cmd parse error from diff dict key")
        has_subgroup, subgroup_name = extract_subgroup_name(test_key)
        self.assertTrue(has_subgroup, "sub group parse failed from diff dict key")
        self.assertEqual(subgroup_name, "acr", "sub group name extract failed")
        has_subgroup_deprecate_prop, subgroup_deprecate_prop = extract_subgroup_deprecate_property(test_key, "deprecate_info")
        self.assertTrue(has_subgroup_deprecate_prop, "sub group deprecate info prop parse failed from diff dict key")
        self.assertEqual(subgroup_deprecate_prop, "hide", "sub group deprecate prop extract failed")

    def test_diff_dict_key_for_subgroups_prop(self):
        test_key = "root['sub_groups']['acr']['deprecate_info_hide']"
        has_cmd, _ = extract_cmd_name(test_key)
        self.assertFalse(has_cmd, "cmd parse error from diff dict key")
        has_subgroup, subgroup_name = extract_subgroup_name(test_key)
        self.assertTrue(has_subgroup, "sub group parse failed from diff dict key")
        self.assertEqual(subgroup_name, "acr", "sub group name extract failed")
        has_subgroup_prop, subgroup_prop = extract_subgroup_property(test_key, subgroup_name)
        self.assertTrue(has_subgroup_prop, "sub group prop parse failed from diff dict key")
        self.assertEqual(subgroup_prop, "deprecate_info_hide", "sub group prop extract failed")

    def test_diff_meta(self):
        base_meta_file = os.path.join(TEST_DIR, "jsons", "az_monitor_meta_before.json")
        diff_meta_file = os.path.join(TEST_DIR, "jsons", "az_monitor_meta_after.json")
        if not os.path.exists(base_meta_file) or not os.path.exists(diff_meta_file):
            raise ValueError("Meta file not found, please check testing package")

        result = meta_diff(base_meta_file=base_meta_file,
                           diff_meta_file=diff_meta_file,
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
        base_meta_file = os.path.join(TEST_DIR, "jsons", "az_ams_meta_before.json")
        diff_meta_file = os.path.join(TEST_DIR, "jsons", "az_ams_meta_after.json")
        if not os.path.exists(base_meta_file) or not os.path.exists(diff_meta_file):
            raise ValueError("Meta file not found, please check testing package")
        result = meta_diff(base_meta_file=base_meta_file,
                           diff_meta_file=diff_meta_file,
                           output_type="text")
        self.assertEqual(result, [], "returned change isn't empty")

    def test_dynamic_diff_meta_whitelist(self):
        base_meta_file = os.path.join(TEST_DIR, "jsons", "az_mysql_meta_before.json")
        diff_meta_file = os.path.join(TEST_DIR, "jsons", "az_mysql_meta_after.json")
        if not os.path.exists(base_meta_file) or not os.path.exists(diff_meta_file):
            raise ValueError("Meta file not found, please check testing package")
        result = meta_diff(base_meta_file=base_meta_file,
                           diff_meta_file=diff_meta_file,
                           output_type="text")
        self.assertEqual(result, [], "returned change isn't empty")

    def test_expand_deprecate_obj(self):
        example_obj = {
            "module_name": "acr",
            "name": "az",
            "commands": {},
            "sub_groups": {
                "acr": {
                    "name": "acr",
                    "commands": {
                        "acr helm list": {
                            "name": "acr helm list",
                            "parameters": [{
                                "name": "resource_group_name",
                                "deprecate_info": {
                                    "redirect": "resource_group_name2",
                                },
                                "options": ["--resource-group", "-g"],
                                "id_part": "resource_group"
                            }, {
                                "name": "password",
                                "options": ["--password", "-p"],
                                "options_deprecate_info": [{
                                    "target": "--password",
                                    "redirect": "--registry-password",
                                }]
                            }]
                        }
                    },
                    "deprecate_info": {
                        "target": "acr",
                        "redirect": "acr3",
                        "hide": True
                    }
                }
            }
        }
        expand_deprecate_obj(example_obj)
        self.assertEqual(example_obj["sub_groups"]["acr"]["deprecate_info_target"], "acr",
                        "deprecate info expand not working properly")
        self.assertEqual(example_obj["sub_groups"]["acr"]["deprecate_info_redirect"], "acr3",
                        "deprecate info expand not working properly")
        self.assertEqual(example_obj["sub_groups"]["acr"]["commands"]["acr helm list"]["parameters"][0]["deprecate_info_redirect"], "resource_group_name2", "deprecate info expand not working properly")

    def test_diff_meta_for_deprecate_info(self):
        base_meta_file = os.path.join(TEST_DIR, "jsons", "az_acr_meta_before.json")
        diff_meta_file = os.path.join(TEST_DIR, "jsons", "az_acr_meta_after.json")
        if not os.path.exists(base_meta_file) or not os.path.exists(diff_meta_file):
            raise ValueError("Meta file not found, please check testing package")

        result = meta_diff(base_meta_file=base_meta_file, diff_meta_file=diff_meta_file, output_type="text")
        target_message = [
            "sub group `acr` added property `deprecate_info_hide` | diff_level: 2",
            "sub group `acr` updated property `deprecate_info_redirect` from `acr2` to `acr3` | diff_level: 1",
            "sub group `acr helm` removed property `deprecate_info_target` | diff_level: 1",
            "sub group `acr helm` removed property `deprecate_info_redirect` | diff_level: 2",
            "cmd `acr helm list` removed property `deprecate_info_target` | diff_level: 1",
            "cmd `acr helm list` removed property `deprecate_info_redirect` | diff_level: 2",
            "cmd `acr helm list` removed property `deprecate_info_hide` | diff_level: 1",
            "cmd `acr helm show` updated property `deprecate_info_redirect` from `acr helm show2` to `acr helm show3` | diff_level: 2",
            "cmd `acr helm list` update parameter `repository`: removed property `options_deprecate_info=",
        ]
        for mes in target_message:
            found = False
            for line in result:
                if line.find(mes) > -1:
                    found = True
                    break
            print(mes)
            self.assertTrue(found, "target message not found")

    def test_diff_meta_with_different_mod_name(self):
        base_meta_file = os.path.join(TEST_DIR, "jsons", "az_virtual-network-manager_meta_before.json")
        diff_meta_file = os.path.join(TEST_DIR, "jsons", "az_network-manager_meta_after.json")
        if not os.path.exists(base_meta_file) or not os.path.exists(diff_meta_file):
            raise ValueError("Meta file not found, please check testing package")
        result = meta_diff(base_meta_file=base_meta_file, diff_meta_file=diff_meta_file, output_type="text")
        target_message = [
            "updated property `name` from `network_manager_scopes` to `module_name`",
        ]
        for mes in target_message:
            found = False
            for line in result:
                if line.find(mes) > -1:
                    found = True
                    break
            self.assertTrue(found, "target message not found")


if __name__ == '__main__':
    unittest.main()
