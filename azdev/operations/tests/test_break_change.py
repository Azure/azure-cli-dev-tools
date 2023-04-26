# -----------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for
# license information.
# -----------------------------------------------------------------------------


import unittest
import os
from azdev.operations.command_change import export_command_meta, cmp_command_meta
from azdev.operations.command_change.util import get_command_tree, extract_cmd_name, \
    extract_cmd_property, extract_para_info


class MyTestCase(unittest.TestCase):

    def test_cmd_meta_generation(self):
        if os.path.exists("./jsons/az_monitor_meta.json"):
            os.remove("./jsons/az_monitor_meta.json")
        module_list = ["monitor"]
        export_command_meta(modules=module_list, meta_output_path="./jsons/")
        self.assertTrue(os.path.exists("./jsons/az_monitor_meta.json"), "new monitor meta generation failed")

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

    def test_diff_meta(self):
        if not os.path.exists("./jsons/az_monitor_meta_before.json") \
                or not os.path.exists("./jsons/az_monitor_meta_after.json"):
            return
        result = cmp_command_meta(base_meta_file="./jsons/az_monitor_meta_before.json",
                         diff_meta_file="./jsons/az_monitor_meta_after.json",
                         output_type="text")
        target_message = "please confirm cmd `monitor private-link-scope scoped-resource show` removed"
        for line in result:
            if line.find(target_message) > -1:
                return
        self.assertTrue(False, "target message not found")


if __name__ == '__main__':
    unittest.main()
