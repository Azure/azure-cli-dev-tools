# -----------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for
# license information.
# -----------------------------------------------------------------------------

from enum import Enum
from .util import extract_cmd_name, extract_cmd_property, extract_para_info
from ..statistics.util import get_command_tree

CMD_PROPERTY_REMOVE_BREAK_LIST = []
CMD_PROPERTY_ADD_BREAK_LIST = ["confirmation"]
CMD_PROPERTY_CHANDE_BREAK_LIST = []
PARA_PROPERTY_REMOVE_BREAK_LIST = ["options"]
PARA_PROPERTY_ADD_BREAK_LIST = ["required"]
PARA_PROPERTY_CHANGE_BREAK_LIST = ["default"]


class ChangeType(Enum):
    DEFAULT = 0
    ADD = 1
    CHANGE = 2
    REMOVE = 3


class MetaDiff:

    def __init__(self, diff_type, is_break=False):
        self.diff_type = diff_type
        self.is_break = is_break
        self.splitter = " "


class CmdMetaDiff(MetaDiff):

    def __init__(self, cmd_name, cmd_property, diff_type=ChangeType.DEFAULT, is_break=False,
                 old_value=None, new_value=None):
        if not cmd_name:
            raise Exception("cmd name needed")
        self.cmd_name = cmd_name
        self.cmd_property = None
        self.old_value = None
        self.new_value = None
        if cmd_property:
            self.cmd_property = cmd_property
            self.cmd_type = "CMD_PROPERTY: "
            if old_value is not None:
                self.old_value = old_value
            if new_value is not None:
                self.new_value = new_value
        else:
            self.cmd_type = "CMD: "
        super().__init__(diff_type, is_break)

    def __str__(self):
        if self.cmd_property:
            if self.old_value is not None and self.new_value is not None:
                res = [self.cmd_type, self.cmd_name, self.cmd_property, self.diff_type,
                       " From ", self.old_value, " to ", self.new_value,
                       "is_break: ", self.is_break]
            else:
                res = [self.cmd_type, self.cmd_name, self.cmd_property, str(self.diff_type), "is_break: ", str(self.is_break)]
        else:
            res = [self.cmd_type, self.cmd_name, str(self.diff_type), "is_break: ", str(self.is_break)]
        return self.splitter.join([str(a) for a in res])


class ParaMetaDiff(MetaDiff):

    def __init__(self, cmd_name, para_name, para_property, diff_type=ChangeType.DEFAULT, is_break=False,
                 old_value=None, new_value=None):
        if not cmd_name:
            raise Exception("cmd name needed")
        self.cmd_name = cmd_name
        self.para_name = None
        self.para_prop = None
        self.old_value = None
        self.new_value = None
        self.para_type = "PARAMETERS:"
        if para_name:
            self.para_name = para_name
            self.para_prop = para_property
            if old_value is not None:
                self.old_value = old_value
            if new_value is not None:
                self.new_value = new_value
        super().__init__(diff_type, is_break)

    def __str__(self):
        if self.para_name:
            if self.old_value is not None and self.new_value is not None:
                res = [self.para_type, self.cmd_name, self.para_name, self.para_prop, str(self.diff_type),
                       " From ", self.old_value, " to ", self.new_value,
                       "is_break: ", str(self.is_break)]
            else:
                res = [self.para_type, self.cmd_name, self.para_name, self.para_prop, str(self.diff_type), "is_break: ", str(self.is_break)]
        else:
            res = [self.para_type, self.cmd_name, str(self.diff_type), "is_break: ", str(self.is_break)]
        return self.splitter.join([str(a) for a in res])


class MetaChangeDetects:

    def __init__(self, deep_diff=None, base_meta=None, diff_meta=None):
        if not deep_diff:
            raise Exception("None diffs from cmd meta json")
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
            diff_obj = ParaMetaDiff(cmd_name, None, diff_type)
            if diff_type == ChangeType.REMOVE:
                # parameter obj remove is breaking
                diff_obj.is_break = True
                self.diff_objs.append(diff_obj)
            elif diff_type == ChangeType.ADD:
                # parameter obj add: check if they are all optional, if required added, is breaking
                is_breaking = False
                cmd_obj = self.__search_cmd_obj(cmd_name, self.diff_meta)
                for para_obj in cmd_obj["parameters"]:
                    if para_obj["required"]:
                        is_breaking = True
                        break
                diff_obj = ParaMetaDiff(cmd_name, None, diff_type, is_breaking)
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
            diff_obj = ParaMetaDiff(cmd_name, para_name, para_property, diff_type)
            if para_property in PARA_PROPERTY_ADD_BREAK_LIST:
                diff_obj.is_break = True
            self.diff_objs.append(diff_obj)
        elif diff_type == ChangeType.REMOVE:
            diff_obj = ParaMetaDiff(cmd_name, para_name, para_property, diff_type)
            if para_property in PARA_PROPERTY_REMOVE_BREAK_LIST:
                diff_obj.is_break = True
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
            if diff_type == ChangeType.ADD:
                cmd_obj = self.__search_cmd_obj(cmd_name, self.diff_meta)
                para_name = cmd_obj["parameters"][para_ind]["name"]
                diff_obj = ParaMetaDiff(cmd_name, para_name, "", diff_type, False, "-", diff_value)
                if cmd_obj.get("required", None):
                    diff_obj.is_break = True
                self.diff_objs.append(diff_obj)
            else:
                cmd_obj = self.__search_cmd_obj(cmd_name, self.base_meta)
                para_name = cmd_obj["parameters"][para_ind]["name"]
                diff_obj = ParaMetaDiff(cmd_name, para_name, "", diff_type, True, diff_value, "-")
                self.diff_objs.append(diff_obj)

        elif len(para_search_res) == 3:
            para_property = para_search_res[1].strip("'")
            if para_property != "options":
                return
            cmd_obj_old = self.__search_cmd_obj(cmd_name, self.base_meta)
            cmd_obj_new = self.__search_cmd_obj(cmd_name, self.diff_meta)
            para_name = cmd_obj_old["parameters"][para_ind]["name"]
            old_options = cmd_obj_old["parameters"][para_ind]["options"]
            new_options = cmd_obj_new["parameters"][para_ind]["options"]
            old_options_value = " ".join(["["] + old_options + ["]"])
            new_options_value = " ".join(["["] + new_options + ["]"])

            if diff_type == ChangeType.ADD:
                diff_obj = ParaMetaDiff(cmd_name, para_name, para_property, diff_type, False,
                                        old_options_value,
                                        new_options_value)
            else:
                diff_obj = ParaMetaDiff(cmd_name, para_name, para_property, diff_type, True,
                                        old_options_value,
                                        new_options_value)
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
        diff_obj = ParaMetaDiff(cmd_name, para_name, para_property, ChangeType.CHANGE, False, old_value, new_value)
        if para_property in PARA_PROPERTY_CHANGE_BREAK_LIST:
            diff_obj.is_break = True
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
                    diff_obj = CmdMetaDiff(cmd_name, cmd_property, diff_type)
                    if cmd_property in CMD_PROPERTY_ADD_BREAK_LIST:
                        diff_obj.is_break = True
                    self.diff_objs.append(diff_obj)
                else:
                    diff_obj = CmdMetaDiff(cmd_name, cmd_property, diff_type)
                    if cmd_property in CMD_PROPERTY_REMOVE_BREAK_LIST:
                        diff_obj.is_break = True
                    self.diff_objs.append(diff_obj)
            else:
                diff_obj = CmdMetaDiff(cmd_name, None, diff_type)
                if diff_type == ChangeType.REMOVE:
                    diff_obj.is_break = True
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
                diff_obj = CmdMetaDiff(cmd_name, cmd_property, ChangeType.CHANGE, False, old_value, new_value)
                if cmd_property in CMD_PROPERTY_CHANDE_BREAK_LIST:
                    diff_obj.is_break = True
                self.diff_objs.append(diff_obj)

    def check_deep_diffs(self):
        self.check_dict_item_remove()
        self.check_dict_item_add()
        self.check_list_item_remove()
        self.check_list_item_add()
        self.check_value_change()

    def export_meta_changes(self):
        for obj in self.diff_objs:
            print(obj)

