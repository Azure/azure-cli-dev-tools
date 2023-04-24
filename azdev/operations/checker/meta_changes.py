# -----------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for
# license information.
# -----------------------------------------------------------------------------

import json
from json import JSONEncoder
from azdev.utilities import get_change_rule_template, get_change_suggest_template


class MetaChangeEncoder(JSONEncoder):
    def default(self, o):
        return o.__dict__


class MetaChange(object):

    def __init__(self, rule_id="1000", is_break=False, rule_message="", suggest_message=""):
        self.rule_id = rule_id
        self.is_break = is_break
        self.rule_message = rule_message
        self.suggest_message = suggest_message

    def __str__(self):
        res = [self.rule_message, "is_break: {0}. ".format(self.is_break)]
        if self.suggest_message:
            res.append(self.suggest_message)
        return "| ".join([str(a) for a in res])


class CmdAdd(MetaChange):
    def __init__(self, cmd_name, is_break=False):
        if not cmd_name:
            raise Exception("cmd name needed")
        self.rule_id = "1001"
        self.cmd_name = cmd_name
        self.is_break = is_break
        self.rule_message = get_change_rule_template(self.rule_id).format(self.cmd_name)
        self.suggest_message = get_change_suggest_template(self.rule_id).format(self.cmd_name) if self.is_break else ""
        super().__init__(self.rule_id, is_break, self.rule_message, self.suggest_message)


class CmdRemove(MetaChange):
    def __init__(self, cmd_name, is_break=True):
        if not cmd_name:
            raise Exception("cmd name needed")
        self.cmd_name = cmd_name
        self.rule_id = "1002"
        self.is_break = is_break
        self.rule_message = get_change_rule_template(self.rule_id).format(self.cmd_name)
        self.suggest_message = get_change_suggest_template(self.rule_id).format(self.cmd_name) if self.is_break else ""
        super().__init__(self.rule_id, is_break, self.rule_message, self.suggest_message)


class CmdPropAdd(MetaChange):
    def __init__(self, cmd_name, cmd_property, is_break=False):
        if not cmd_name or not cmd_property:
            raise Exception("cmd name needed")
        self.rule_id = "1003"
        self.cmd_name = cmd_name
        self.cmd_property = cmd_property
        self.is_break = is_break
        self.rule_message = get_change_rule_template(self.rule_id).format(self.cmd_name, self.cmd_property)
        self.suggest_message = get_change_suggest_template(self.rule_id).format(self.cmd_property, self.cmd_name) \
            if self.is_break else ""
        super().__init__(self.rule_id, is_break, self.rule_message, self.suggest_message)


class CmdPropRemove(MetaChange):
    def __init__(self, cmd_name, cmd_property, is_break=False):
        if not cmd_name or not cmd_property:
            raise Exception("cmd name needed")
        self.rule_id = "1004"
        self.cmd_name = cmd_name
        self.cmd_property = cmd_property
        self.is_break = is_break
        self.rule_message = get_change_rule_template(self.rule_id).format(self.cmd_name, self.cmd_property)
        self.suggest_message = get_change_suggest_template(self.rule_id).format(self.cmd_property, self.cmd_name) \
            if self.is_break else ""
        super().__init__(self.rule_id, is_break, self.rule_message, self.suggest_message)


class CmdPropUpdate(MetaChange):

    def __init__(self, cmd_name, cmd_property, is_break=False, old_value=None, new_value=None):
        if not cmd_name or not cmd_property:
            raise Exception("cmd name and cmd prop needed")
        self.rule_id = "1005"
        self.cmd_name = cmd_name
        self.is_break = is_break
        self.cmd_prop_updated = cmd_property
        self.old_value = ""
        self.new_value = ""

        if old_value is not None:
            self.old_value = old_value
        if new_value is not None:
            self.new_value = new_value
        self.rule_message = get_change_rule_template(self.rule_id).format(self.cmd_name, self.cmd_prop_updated,
                                                                          self.old_value, self.new_value)
        self.suggest_message = get_change_suggest_template(self.rule_id).format(self.cmd_prop_updated,
                                                                                self.new_value, self.old_value,
                                                                                self.cmd_name) if self.is_break else ""
        super().__init__(self.rule_id, is_break, self.rule_message, self.suggest_message)


class ParaAdd(MetaChange):

    def __init__(self, cmd_name, para_name, is_break=False):
        if not cmd_name or not para_name:
            raise Exception("cmd name, parameter name needed")
        self.rule_id = "1006"
        self.cmd_name = cmd_name
        self.para_name = para_name
        self.is_break = is_break
        self.rule_message = get_change_rule_template(self.rule_id).format(self.cmd_name, self.para_name)
        self.suggest_message = get_change_suggest_template(self.rule_id).format(self.para_name,
                                                                                self.cmd_name) if self.is_break else ""
        super().__init__(self.rule_id, is_break, self.rule_message, self.suggest_message)


class ParaRemove(MetaChange):

    def __init__(self, cmd_name, para_name, is_break=False):
        if not cmd_name or not para_name:
            raise Exception("cmd name, parameter name needed")
        self.rule_id = "1007"
        self.cmd_name = cmd_name
        self.para_name = para_name
        self.is_break = is_break
        self.rule_message = get_change_rule_template(self.rule_id).format(self.cmd_name, self.para_name)
        self.suggest_message = get_change_suggest_template(self.rule_id).format(self.para_name,
                                                                                self.cmd_name) if self.is_break else ""
        super().__init__(self.rule_id, is_break, self.rule_message, self.suggest_message)


class ParaPropAdd(MetaChange):

    def __init__(self, cmd_name, para_name, para_property, is_break=False):
        if not cmd_name or not para_name or not para_property:
            raise Exception("cmd name, parameter name and parameter property needed")
        self.rule_id = "1008"
        self.cmd_name = cmd_name
        self.para_name = para_name
        self.para_prop = para_property
        self.is_break = is_break

        self.rule_message = get_change_rule_template(self.rule_id).format(self.cmd_name, self.para_name,
                                                                          self.para_prop)
        self.suggest_message = get_change_suggest_template(self.rule_id).format(self.para_prop,
                                                                                self.para_name,
                                                                                self.cmd_name) if self.is_break else ""
        super().__init__(self.rule_id, is_break, self.rule_message, self.suggest_message)


class ParaPropRemove(MetaChange):

    def __init__(self, cmd_name, para_name, para_property, is_break=False):
        if not cmd_name or not para_name or not para_property:
            raise Exception("cmd name, parameter name and parameter property needed")
        self.rule_id = "1009"
        self.cmd_name = cmd_name
        self.para_name = para_name
        self.para_prop = para_property
        self.is_break = is_break

        self.rule_message = get_change_rule_template(self.rule_id).format(self.cmd_name, self.para_name,
                                                                          self.para_prop)
        self.suggest_message = get_change_suggest_template(self.rule_id).format(self.para_prop,
                                                                                self.para_name,
                                                                                self.cmd_name) if self.is_break else ""
        super().__init__(self.rule_id, is_break, self.rule_message, self.suggest_message)


class ParaPropUpdate(MetaChange):

    def __init__(self, cmd_name, para_name, para_property, is_break=False, old_value=None, new_value=None):
        if not cmd_name or not para_name or not para_property:
            raise Exception("cmd name, parameter name and parameter property needed")
        self.rule_id = "1010"
        self.cmd_name = cmd_name
        self.para_name = para_name
        self.para_prop_updated = para_property
        self.is_break = is_break
        self.old_value = None
        self.new_value = None
        if old_value is not None:
            self.old_value = old_value
        if new_value is not None:
            self.new_value = new_value

        self.rule_message = get_change_rule_template(self.rule_id).format(self.cmd_name, self.para_name,
                                                                          self.para_prop_updated,
                                                                          self.old_value, self.new_value)
        self.suggest_message = get_change_suggest_template(self.rule_id).format(self.para_prop_updated,
                                                                                self.new_value, self.old_value,
                                                                                self.para_name,
                                                                                self.cmd_name) if self.is_break else ""
        super().__init__(self.rule_id, is_break, self.rule_message, self.suggest_message)


if __name__ == '__main__':
    diff = CmdPropUpdate("monitor private-link-scope scoped-resource show", "is_aaz", False, False, True)
    # encode object into json
    # refer: https://pynative.com/python-convert-json-data-into-custom-python-object/

    diff_json = json.dumps(diff, cls=MetaChangeEncoder, indent=4)
    print(diff_json)
    diff_json_loaded = json.loads(diff_json)
    print(" print : ", str(diff))
    for attr, value in diff.__dict__.items():
        if attr not in ["rule_id", "is_break", "rule_message", "suggest_message"]:
            print(attr, getattr(diff, attr))



