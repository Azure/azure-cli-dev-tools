# -----------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for
# license information.
# -----------------------------------------------------------------------------

from .utils import get_change_rule_template, get_change_suggest_template, DiffLevel
from ._const import BREAKING_CHANE_RULE_LINK_URL_PREFIX, BREAKING_CHANE_RULE_LINK_URL_SUFFIX, \
    SUBGROUP_PROPERTY_IGNORED_LIST, CMD_PROPERTY_IGNORED_LIST, PARA_NAME_IGNORED_LIST, \
    PARA_PROPERTY_IGNORED_LIST, PARA_VALUE_IGNORED_LIST


class MetaChange:

    def __init__(self, rule_id="1000", is_break=False, diff_level=DiffLevel.INFO, rule_message="", suggest_message="",
                 is_ignore=False, filter_key=None):
        self.rule_id = rule_id
        self.is_break = is_break
        self.diff_level = diff_level
        self.rule_message = rule_message
        self.suggest_message = suggest_message
        self.rule_link_url = BREAKING_CHANE_RULE_LINK_URL_PREFIX + self.rule_id + BREAKING_CHANE_RULE_LINK_URL_SUFFIX
        self.is_ignore = is_ignore
        self.filter_key = filter_key

    def __str__(self):
        res = [self.rule_message, "diff_level: " + str(self.diff_level.value)]
        if self.is_break:
            res.append("is_break: {0}".format(self.is_break))
            res.append(self.suggest_message)
        return " | ".join([str(a) for a in res])


class SubgroupAdd(MetaChange):
    def __init__(self, subgroup_name, is_break=False, diff_level=DiffLevel.INFO):
        if not subgroup_name:
            raise Exception("sub group name needed")
        self.rule_id = "1011"
        self.subgroup_name = subgroup_name
        self.is_break = is_break
        self.diff_level = diff_level
        self.rule_message = get_change_rule_template(self.rule_id).format(self.subgroup_name)
        self.suggest_message = get_change_suggest_template(self.rule_id).format(self.subgroup_name) \
            if self.is_break else ""
        super().__init__(self.rule_id, is_break, diff_level, self.rule_message, self.suggest_message)


class SubgroupRemove(MetaChange):
    def __init__(self, subgroup_name, is_break=True, diff_level=DiffLevel.BREAK):
        if not subgroup_name:
            raise Exception("sub group name needed")
        self.rule_id = "1012"
        self.subgroup_name = subgroup_name
        self.is_break = is_break
        self.diff_level = diff_level
        self.rule_message = get_change_rule_template(self.rule_id).format(self.subgroup_name)
        self.suggest_message = get_change_suggest_template(self.rule_id).format(self.subgroup_name) \
            if self.is_break else ""
        super().__init__(self.rule_id, is_break, diff_level, self.rule_message, self.suggest_message)


class SubgroupPropAdd(MetaChange):
    def __init__(self, subgroup_name, subgroup_property, is_break=False, diff_level=DiffLevel.INFO):
        if not subgroup_name or not subgroup_property:
            raise Exception("sub group name needed")
        self.rule_id = "1013"
        self.is_ignore = False
        self.subgroup_name = subgroup_name
        self.subgroup_property = subgroup_property
        self.is_break = is_break
        self.diff_level = diff_level
        self.rule_message = get_change_rule_template(self.rule_id).format(self.subgroup_name, self.subgroup_property)
        self.suggest_message = get_change_suggest_template(self.rule_id).format(self.subgroup_property, self.subgroup_name) \
            if self.is_break else ""
        if subgroup_property in SUBGROUP_PROPERTY_IGNORED_LIST:
            self.is_ignore = True
        self.filter_key = [self.rule_id, self.subgroup_name, self.subgroup_property]
        super().__init__(self.rule_id, is_break, diff_level, self.rule_message, self.suggest_message, self.is_ignore,
                         self.filter_key)


class SubgroupPropRemove(MetaChange):
    def __init__(self, subgroup_name, subgroup_property, is_break=False, diff_level=DiffLevel.BREAK):
        if not subgroup_name or not subgroup_property:
            raise Exception("sub group name needed")
        self.rule_id = "1014"
        self.is_ignore = False
        self.subgroup_name = subgroup_name
        self.subgroup_property = subgroup_property
        self.is_break = is_break
        self.diff_level = diff_level
        self.rule_message = get_change_rule_template(self.rule_id).format(self.subgroup_name, self.subgroup_property)
        if self.is_break:
            self.suggest_message = get_change_suggest_template(self.rule_id).format(self.subgroup_property,
                                                                                    self.subgroup_name)
        else:
            self.suggest_message = ""
        if subgroup_property in CMD_PROPERTY_IGNORED_LIST:
            self.is_ignore = True
        self.filter_key = [self.rule_id, self.subgroup_name, self.subgroup_property]
        super().__init__(self.rule_id, is_break, diff_level, self.rule_message, self.suggest_message,
                         self.is_ignore, self.filter_key)


class SubgroupPropUpdate(MetaChange):

    def __init__(self, subgroup_name, subgroup_property, is_break=False, diff_level=DiffLevel.INFO,
                 old_value=None, new_value=None):
        if not subgroup_name or not subgroup_property:
            raise Exception("sub group name and sub group prop needed")
        self.rule_id = "1015"
        self.is_ignore = False
        self.subgroup_name = subgroup_name
        self.is_break = is_break
        self.diff_level = diff_level
        self.subgroup_prop_updated = subgroup_property
        self.old_value = ""
        self.new_value = ""

        if old_value is not None:
            self.old_value = old_value
        if new_value is not None:
            self.new_value = new_value
        self.rule_message = get_change_rule_template(self.rule_id).format(self.subgroup_name,
                                                                          self.subgroup_prop_updated,
                                                                          self.old_value, self.new_value)
        if self.is_break:
            self.suggest_message = get_change_suggest_template(self.rule_id).format(self.subgroup_prop_updated,
                                                                                    self.new_value, self.old_value,
                                                                                    self.subgroup_name)
        else:
            self.suggest_message = ""
        if subgroup_property in SUBGROUP_PROPERTY_IGNORED_LIST:
            self.is_ignore = True
        self.filter_key = [self.rule_id, self.subgroup_name, self.subgroup_prop_updated]
        super().__init__(self.rule_id, is_break, diff_level, self.rule_message, self.suggest_message,
                         self.is_ignore, self.filter_key)


class CmdAdd(MetaChange):
    def __init__(self, cmd_name, is_break=False, diff_level=DiffLevel.INFO):
        if not cmd_name:
            raise Exception("cmd name needed")
        self.rule_id = "1001"
        self.cmd_name = cmd_name
        self.is_break = is_break
        self.diff_level = diff_level
        self.rule_message = get_change_rule_template(self.rule_id).format(self.cmd_name)
        self.suggest_message = get_change_suggest_template(self.rule_id).format(self.cmd_name) if self.is_break else ""
        super().__init__(self.rule_id, is_break, diff_level, self.rule_message, self.suggest_message)


class CmdRemove(MetaChange):
    def __init__(self, cmd_name, is_break=True, diff_level=DiffLevel.BREAK):
        if not cmd_name:
            raise Exception("cmd name needed")
        self.cmd_name = cmd_name
        self.rule_id = "1002"
        self.is_break = is_break
        self.diff_level = diff_level
        self.rule_message = get_change_rule_template(self.rule_id).format(self.cmd_name)
        self.suggest_message = get_change_suggest_template(self.rule_id).format(self.cmd_name) if self.is_break else ""
        super().__init__(self.rule_id, is_break, diff_level, self.rule_message, self.suggest_message)


class CmdPropAdd(MetaChange):
    def __init__(self, cmd_name, cmd_property, is_break=False, diff_level=DiffLevel.INFO):
        if not cmd_name or not cmd_property:
            raise Exception("cmd name needed")
        self.rule_id = "1003"
        self.is_ignore = False
        self.cmd_name = cmd_name
        self.cmd_property = cmd_property
        self.is_break = is_break
        self.diff_level = diff_level
        self.rule_message = get_change_rule_template(self.rule_id).format(self.cmd_name, self.cmd_property)
        self.suggest_message = get_change_suggest_template(self.rule_id).format(self.cmd_property, self.cmd_name) \
            if self.is_break else ""
        if cmd_property in CMD_PROPERTY_IGNORED_LIST:
            self.is_ignore = True
        self.filter_key = [self.rule_id, self.cmd_name, self.cmd_property]
        super().__init__(self.rule_id, is_break, diff_level, self.rule_message, self.suggest_message, self.is_ignore,
                         self.filter_key)


class CmdPropRemove(MetaChange):
    def __init__(self, cmd_name, cmd_property, is_break=False, diff_level=DiffLevel.BREAK):
        if not cmd_name or not cmd_property:
            raise Exception("cmd name needed")
        self.rule_id = "1004"
        self.is_ignore = False
        self.cmd_name = cmd_name
        self.cmd_property = cmd_property
        self.is_break = is_break
        self.diff_level = diff_level
        self.rule_message = get_change_rule_template(self.rule_id).format(self.cmd_name, self.cmd_property)
        self.suggest_message = get_change_suggest_template(self.rule_id).format(self.cmd_property, self.cmd_name) \
            if self.is_break else ""
        if cmd_property in CMD_PROPERTY_IGNORED_LIST:
            self.is_ignore = True
        self.filter_key = [self.rule_id, self.cmd_name, self.cmd_property]
        super().__init__(self.rule_id, is_break, diff_level, self.rule_message, self.suggest_message,
                         self.is_ignore, self.filter_key)


class CmdPropUpdate(MetaChange):

    def __init__(self, cmd_name, cmd_property, is_break=False, diff_level=DiffLevel.INFO,
                 old_value=None, new_value=None):
        if not cmd_name or not cmd_property:
            raise Exception("cmd name and cmd prop needed")
        self.rule_id = "1005"
        self.is_ignore = False
        self.cmd_name = cmd_name
        self.is_break = is_break
        self.diff_level = diff_level
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
        if cmd_property in CMD_PROPERTY_IGNORED_LIST:
            self.is_ignore = True
        self.filter_key = [self.rule_id, self.cmd_name, self.cmd_prop_updated]
        super().__init__(self.rule_id, is_break, diff_level, self.rule_message, self.suggest_message,
                         self.is_ignore, self.filter_key)


class ParaAdd(MetaChange):

    def __init__(self, cmd_name, para_name, is_break=False, diff_level=DiffLevel.INFO):
        if not cmd_name or not para_name:
            raise Exception("cmd name, parameter name needed")
        self.rule_id = "1006"
        self.cmd_name = cmd_name
        self.para_name = para_name
        self.is_break = is_break
        self.diff_level = diff_level
        self.rule_message = get_change_rule_template(self.rule_id).format(self.cmd_name, self.para_name)
        self.suggest_message = get_change_suggest_template(self.rule_id).format(self.para_name,
                                                                                self.cmd_name) if self.is_break else ""
        super().__init__(self.rule_id, is_break, diff_level, self.rule_message, self.suggest_message)


class ParaRemove(MetaChange):

    def __init__(self, cmd_name, para_name, is_break=False, diff_level=DiffLevel.BREAK):
        if not cmd_name or not para_name:
            raise Exception("cmd name, parameter name needed")
        self.rule_id = "1007"
        self.cmd_name = cmd_name
        self.para_name = para_name
        self.is_break = is_break
        self.diff_level = diff_level
        self.rule_message = get_change_rule_template(self.rule_id).format(self.cmd_name, self.para_name)
        self.suggest_message = get_change_suggest_template(self.rule_id).format(self.para_name,
                                                                                self.cmd_name) if self.is_break else ""
        super().__init__(self.rule_id, is_break, diff_level, self.rule_message, self.suggest_message)


class ParaPropAdd(MetaChange):

    def __init__(self, cmd_name, para_name, para_property, para_prop_value, is_break=False, diff_level=DiffLevel.INFO):
        if not cmd_name or not para_name or not para_property:
            raise Exception("cmd name, parameter name and parameter property needed")
        self.rule_id = "1008"
        self.is_ignore = False
        self.cmd_name = cmd_name
        self.para_name = para_name
        self.para_prop = para_property
        self.para_prop_value = para_prop_value
        self.is_break = is_break
        self.diff_level = diff_level

        self.rule_message = get_change_rule_template(self.rule_id).format(self.cmd_name, self.para_name,
                                                                          self.para_prop, self.para_prop_value)
        self.suggest_message = get_change_suggest_template(self.rule_id).format(self.para_prop,
                                                                                self.para_prop_value,
                                                                                self.para_name,
                                                                                self.cmd_name) if self.is_break else ""
        if para_property in PARA_PROPERTY_IGNORED_LIST or para_name in PARA_NAME_IGNORED_LIST:
            self.is_ignore = True
        super().__init__(self.rule_id, is_break, diff_level, self.rule_message, self.suggest_message, self.is_ignore)


class ParaPropRemove(MetaChange):

    def __init__(self, cmd_name, para_name, para_property, para_prop_value, is_break=False, diff_level=DiffLevel.BREAK):
        if not cmd_name or not para_name or not para_property:
            raise Exception("cmd name, parameter name and parameter property needed")
        self.rule_id = "1009"
        self.is_ignore = False
        self.cmd_name = cmd_name
        self.para_name = para_name
        self.para_prop = para_property
        self.para_prop_value = para_prop_value
        self.is_break = is_break
        self.diff_level = diff_level

        self.rule_message = get_change_rule_template(self.rule_id).format(self.cmd_name, self.para_name,
                                                                          self.para_prop, self.para_prop_value)
        self.suggest_message = get_change_suggest_template(self.rule_id).format(self.para_prop,
                                                                                self.para_prop_value,
                                                                                self.para_name,
                                                                                self.cmd_name) if self.is_break else ""
        if para_property in PARA_PROPERTY_IGNORED_LIST or para_name in PARA_NAME_IGNORED_LIST:
            self.is_ignore = True
        super().__init__(self.rule_id, is_break, diff_level, self.rule_message, self.suggest_message, self.is_ignore)


class ParaPropUpdate(MetaChange):

    def __init__(self, cmd_name, para_name, para_property, is_break=False, diff_level=DiffLevel.INFO,
                 old_value=None, new_value=None):
        if not cmd_name or not para_name or not para_property:
            raise Exception("cmd name, parameter name and parameter property needed")
        self.rule_id = "1010"
        self.is_ignore = False
        self.cmd_name = cmd_name
        self.para_name = para_name
        self.para_prop_updated = para_property
        self.is_break = is_break
        self.diff_level = diff_level
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
        if para_property in PARA_PROPERTY_IGNORED_LIST or para_name in PARA_NAME_IGNORED_LIST:
            self.is_ignore = True
        if self.new_value in PARA_VALUE_IGNORED_LIST or self.old_value in PARA_VALUE_IGNORED_LIST:
            self.is_ignore = True
        self.filter_key = [self.rule_id, self.cmd_name, self.para_name, self.para_prop_updated]
        super().__init__(self.rule_id, is_break, diff_level, self.rule_message, self.suggest_message,
                         self.is_ignore, self.filter_key)
