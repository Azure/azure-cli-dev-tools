# -----------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for
# license information.
# -----------------------------------------------------------------------------

from .util import extract_cmd_name, extract_cmd_property, extract_para_info, ChangeType
from ..statistics.util import get_command_tree
from .meta_changes import (CmdAdd, CmdRemove, CmdPropAdd, CmdPropRemove, CmdPropUpdate, ParaAdd, ParaRemove,
                           ParaPropAdd, ParaPropRemove, ParaPropUpdate)

from azdev.utilities import (CMD_PROPERTY_ADD_BREAK_LIST, CMD_PROPERTY_REMOVE_BREAK_LIST,
                             CMD_PROPERTY_UPDATE_BREAK_LIST, PARA_PROPERTY_REMOVE_BREAK_LIST,
                             PARA_PROPERTY_ADD_BREAK_LIST, PARA_PROPERTY_UPDATE_BREAK_LIST)


class MetaChangeDetects:

    EXPORTED_PROP = ["rule_id", "is_break", "rule_message", "suggest_message", "cmd_name"]

    def __init__(self, deep_diff=None, base_meta=None, diff_meta=None):
        if not deep_diff:
            raise Exception("None diffs from cmd meta json")
        assert base_meta["module_name"] == diff_meta["module_name"]
        self.module_name = base_meta["module_name"]
        self.deep_diff = deep_diff
        self.base_meta = base_meta
        self.diff_meta = diff_meta
        self.diff_objs = []

    def __search_cmd_obj(self, cmd_name, search_meta):
        command_tree = get_command_tree(cmd_name)
        meta_search = search_meta
        while True:
            if "is_group" not in command_tree:
                break
            if command_tree["is_group"]:
                group_name = command_tree["group_name"]
                meta_search = meta_search["sub_groups"][group_name]
                command_tree = command_tree["sub_info"]
            else:
                cmd_name = command_tree["cmd_name"]
                meta_search = meta_search["commands"][cmd_name]
                break
        return meta_search

    def __process_dict_item_cmd_parameters(self, dict_key, cmd_name, diff_type):
        para_search_res = extract_para_info(dict_key)
        if not para_search_res:
            if diff_type == ChangeType.REMOVE:
                # parameter obj remove is breaking
                # todo test
                cmd_obj = self.__search_cmd_obj(cmd_name, self.base_meta_meta)
                para_name_arr = [para_obj['name'] for para_obj in cmd_obj["parameters"]]
                diff_obj = ParaRemove(cmd_name, ",".join(para_name_arr), True)
                self.diff_objs.append(diff_obj)
            elif diff_type == ChangeType.ADD:
                # parameter obj add: check if they are all optional, if one required parameter added, is breaking
                is_breaking = False
                required_para_name = None
                cmd_obj = self.__search_cmd_obj(cmd_name, self.diff_meta)
                for para_obj in cmd_obj["parameters"]:
                    if para_obj["required"]:
                        is_breaking = True
                        required_para_name = para_obj['name']
                        break
                diff_obj = ParaAdd(cmd_name, required_para_name, is_breaking)
                self.diff_objs.append(diff_obj)
            return
        try:
            para_ind = int(para_search_res[0])
        except Exception as e:
            pass
        cmd_obj = self.__search_cmd_obj(cmd_name, self.base_meta)
        para_name = cmd_obj["parameters"][para_ind]["name"]
        para_property = para_search_res[1].strip("'")
        if diff_type == ChangeType.ADD:
            if para_property in PARA_PROPERTY_ADD_BREAK_LIST:
                diff_obj = ParaPropAdd(cmd_name, para_name, para_property, True)
            else:
                diff_obj = ParaPropAdd(cmd_name, para_name, para_property, False)
            self.diff_objs.append(diff_obj)
        elif diff_type == ChangeType.REMOVE:
            if para_property in PARA_PROPERTY_REMOVE_BREAK_LIST:
                diff_obj = ParaPropRemove(cmd_name, para_name, para_property, True)
            else:
                diff_obj = ParaPropRemove(cmd_name, para_name, para_property, False)
            self.diff_objs.append(diff_obj)

    def __process_list_item_cmd_parameters(self, dict_key, cmd_name, diff_type, diff_value):
        para_search_res = extract_para_info(dict_key)
        if not para_search_res:
            # inapplicable
            return
        try:
            para_ind = int(para_search_res[0])
        except Exception as e:
            pass

        if len(para_search_res) == 1:
            # todo check options diff incase just name changes
            if diff_type == ChangeType.ADD:
                cmd_obj = self.__search_cmd_obj(cmd_name, self.diff_meta)
                para_name = cmd_obj["parameters"][para_ind]["name"]
                if cmd_obj.get("required", None):
                    diff_obj = ParaAdd(cmd_name, para_name, True)
                else:
                    diff_obj = ParaAdd(cmd_name, para_name, False)
                self.diff_objs.append(diff_obj)
            else:
                cmd_obj = self.__search_cmd_obj(cmd_name, self.base_meta)
                para_name = cmd_obj["parameters"][para_ind]["name"]
                diff_obj = ParaRemove(cmd_name, para_name, True)
                self.diff_objs.append(diff_obj)

        elif len(para_search_res) == 3:
            para_property = para_search_res[1].strip("'")
            # todo check choices
            if para_property not in ["options", "choices"]:
                return
            cmd_obj_old = self.__search_cmd_obj(cmd_name, self.base_meta)
            cmd_obj_new = self.__search_cmd_obj(cmd_name, self.diff_meta)
            para_name = cmd_obj_old["parameters"][para_ind]["name"]
            old_list = cmd_obj_old["parameters"][para_ind][para_property]
            new_list = cmd_obj_new["parameters"][para_ind][para_property]
            old_options_value = " ".join(["["] + old_list + ["]"])
            new_options_value = " ".join(["["] + new_list + ["]"])

            if diff_type == ChangeType.ADD:
                diff_obj = ParaPropUpdate(cmd_name, para_name, para_property, False, old_options_value,
                                          new_options_value)
            else:
                diff_obj = ParaPropUpdate(cmd_name, para_name, para_property, True, old_options_value, new_options_value)
            self.diff_objs.append(diff_obj)

    def __process_value_change_cmd_parameters(self, dict_key, cmd_name, old_value, new_value):
        para_search_res = extract_para_info(dict_key)
        if not para_search_res:
            # inapplicable
            return
        try:
            para_ind = int(para_search_res[0])
        except Exception as e:
            pass
        cmd_obj = self.__search_cmd_obj(cmd_name, self.base_meta)
        para_name = cmd_obj["parameters"][para_ind]["name"]
        para_property = para_search_res[1].strip("'")
        if para_property in PARA_PROPERTY_UPDATE_BREAK_LIST:
            diff_obj = ParaPropUpdate(cmd_name, para_name, para_property, True, old_value, new_value)
        else:
            diff_obj = ParaPropUpdate(cmd_name, para_name, para_property, False, old_value, new_value)
        self.diff_objs.append(diff_obj)

    def __iter_dict_items(self, dict_items, diff_type):
        if diff_type != ChangeType.REMOVE and diff_type != ChangeType.ADD:
            raise Exception("Unsupported dict item type")

        for dict_key in dict_items:
            has_cmd, cmd_name = extract_cmd_name(dict_key)
            if not has_cmd or not cmd_name:
                print("extract cmd failed for " + dict_key)
                continue

            has_cmd_key, cmd_property = extract_cmd_property(dict_key, cmd_name)
            if has_cmd_key:
                if cmd_property == "parameters":
                    self.__process_dict_item_cmd_parameters(dict_key, cmd_name, diff_type)
                elif diff_type == ChangeType.ADD:
                    if cmd_property in CMD_PROPERTY_ADD_BREAK_LIST:
                        diff_obj = CmdPropAdd(cmd_name, cmd_property, True)
                    else:
                        diff_obj = CmdPropAdd(cmd_name, cmd_property, True)
                    self.diff_objs.append(diff_obj)
                else:
                    if cmd_property in CMD_PROPERTY_REMOVE_BREAK_LIST:
                        diff_obj = CmdPropRemove(cmd_name, cmd_property, True)
                    else:
                        diff_obj = CmdPropRemove(cmd_name, cmd_property, False)
                    self.diff_objs.append(diff_obj)
            else:
                if diff_type == ChangeType.REMOVE:
                    diff_obj = CmdRemove(cmd_name)
                else:
                    diff_obj = CmdAdd(cmd_name)

                self.diff_objs.append(diff_obj)

    def __iter_list_items(self, list_items, diff_type):
        """
        ['parameters'][0]['options'][1]
        ['parameters'][3]
        """
        if diff_type != ChangeType.REMOVE and diff_type != ChangeType.ADD:
            raise Exception("Unsupported dict item type")

        for key, value in list_items.items():
            has_cmd, cmd_name = extract_cmd_name(key)
            if not has_cmd or not cmd_name:
                print("extract cmd failed for " + key)
                continue
            has_cmd_key, cmd_property = extract_cmd_property(key, cmd_name)
            if not has_cmd_key:
                continue
            if cmd_property == "parameters":
                self.__process_list_item_cmd_parameters(key, cmd_name, diff_type, value)

    def check_dict_item_remove(self):
        if not self.deep_diff.get("dictionary_item_removed", None):
            return
        dict_item_removed = self.deep_diff["dictionary_item_removed"]
        self.__iter_dict_items(dict_item_removed, ChangeType.REMOVE)

    def check_dict_item_add(self):
        if not self.deep_diff.get("dictionary_item_added", None):
            return
        dict_item_added = self.deep_diff["dictionary_item_added"]
        self.__iter_dict_items(dict_item_added, ChangeType.ADD)

    def check_list_item_remove(self):
        if not self.deep_diff.get("iterable_item_removed", None):
            return

        list_item_remove = self.deep_diff["iterable_item_removed"]
        self.__iter_list_items(list_item_remove, ChangeType.REMOVE)

    def check_list_item_add(self):
        if not self.deep_diff.get("iterable_item_added", None):
            return
        list_item_add = self.deep_diff["iterable_item_added"]
        self.__iter_list_items(list_item_add, ChangeType.ADD)

    def check_value_change(self):
        if not self.deep_diff.get("values_changed", None):
            return
        value_changes = self.deep_diff["values_changed"]
        for key, value_obj in value_changes.items():
            old_value = value_obj["old_value"]
            new_value = value_obj["new_value"]
            has_cmd, cmd_name = extract_cmd_name(key)
            if not has_cmd or not cmd_name:
                print("extract cmd failed for " + key)
                continue

            has_cmd_prop, cmd_property = extract_cmd_property(key, cmd_name)
            if not has_cmd_prop:
                return
            if cmd_property == "parameters":
                self.__process_value_change_cmd_parameters(key, cmd_name, old_value, new_value)
            else:
                if cmd_property in CMD_PROPERTY_UPDATE_BREAK_LIST:
                    diff_obj = CmdPropUpdate(cmd_name, cmd_property, True, old_value, new_value)
                else:
                    diff_obj = CmdPropUpdate(cmd_name, cmd_property, False, old_value, new_value)
                self.diff_objs.append(diff_obj)

    def check_deep_diffs(self):
        self.check_dict_item_remove()
        self.check_dict_item_add()
        self.check_list_item_remove()
        self.check_list_item_add()
        self.check_value_change()

    def export_meta_changes(self, only_break, as_tree):
        ret_obj = []
        ret_txt = []
        ret_mod = {
            "module_name": self.module_name,
            "name": "az",
            "commands": {},
            "sub_groups": {}
        }
        for obj in self.diff_objs:
            if only_break and not obj.is_break:
                continue
            ret = {}
            for prop in self.EXPORTED_PROP:
                ret[prop] = getattr(obj, prop)
            ret["rule_name"] = obj.__class__.__name__
            ret_obj.append(ret)
            ret_txt.append(str(obj))
            if not as_tree:
                continue
            command_tree = get_command_tree(obj.cmd_name)
            command_group_info = ret_mod
            while True:
                if "is_group" not in command_tree:
                    break
                if command_tree["is_group"]:
                    group_name = command_tree["group_name"]
                    if group_name not in command_group_info["sub_groups"]:
                        command_group_info["sub_groups"][group_name] = {
                            "name": group_name,
                            "commands": {},
                            "sub_groups": {}
                        }
                    command_tree = command_tree["sub_info"]
                    command_group_info = command_group_info["sub_groups"][group_name]
                else:
                    cmd_name = command_tree["cmd_name"]
                    command_rules = []
                    if cmd_name in command_group_info["commands"]:
                        command_rules = command_group_info["commands"][cmd_name]
                    command_rules.append(ret)
                    command_group_info["commands"][cmd_name] = command_rules
                    break

        return ret_txt, ret_obj, ret_mod



