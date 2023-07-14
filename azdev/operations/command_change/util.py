# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

import json
import os
import re
import jsbeautifier
from enum import Enum
from knack.log import get_logger

logger = get_logger(__name__)

SUBGROUP_NAME_PATTERN = re.compile(r"\[\'sub_groups\'\]\[\'([a-zA-Z0-9\-\s]+)\'\]")
CMD_NAME_PATTERN = re.compile(r"\[\'commands\'\]\[\'([a-zA-Z0-9\-\s]+)\'\]")
CMD_PARAMETER_PROPERTY_PATTERN = re.compile(r"\[(.*?)\]")


class ChangeType(int, Enum):
    DEFAULT = 0
    ADD = 1
    CHANGE = 2
    REMOVE = 3


def get_command_tree(command_name):
    """
    input: monitor log-profiles create
    ret:
    {
        is_group: True,
        group_name: 'monitor',
        sub_info: {
            is_group: True,
            group_name: 'monitor log-profiles',
            sub_info: {
                is_group: False,
                cmd_name: 'monitor log-profiles create'
            }
        }
    }
    """
    name_arr = command_name.split()
    ret = {}
    name_arr.reverse()
    for i, _ in enumerate(name_arr):
        tmp = {}
        if i == 0:
            tmp = {
                "is_group": False,
                "cmd_name": " ".join(name_arr[::-1])
            }
        else:
            tmp = {
                "is_group": True,
                "group_name": " ".join(name_arr[len(name_arr): (i - 1): -1]),
                "sub_info": ret
            }
        ret = tmp
    return ret


def extract_subgroup_name(key):
    subgroup_ame_res = re.findall(SUBGROUP_NAME_PATTERN, key)
    if not subgroup_ame_res or len(subgroup_ame_res) == 0:
        return False, None
    return True, subgroup_ame_res[-1]


def extract_cmd_name(key):
    cmd_name_res = re.findall(CMD_NAME_PATTERN, key)
    if not cmd_name_res or len(cmd_name_res) == 0:
        return False, None
    return True, cmd_name_res[0]


def extract_cmd_property(key, cmd_name):
    cmd_key_pattern = re.compile(cmd_name + r"\'\]\[\'([a-zA-Z0-9\-\_]+)\'\]")
    cmd_key_res = re.findall(cmd_key_pattern, key)
    if not cmd_key_res or len(cmd_key_res) == 0:
        return False, None
    return True, cmd_key_res[0]


def extract_para_info(key):
    parameters_ind = key.find("['parameters']")
    property_ind = key.find("[", parameters_ind + 1)
    property_res = re.findall(CMD_PARAMETER_PROPERTY_PATTERN, key[property_ind:])
    if not property_res:
        return None
    return property_res


def export_meta_changes_to_json(output, output_file):
    if not output_file:
        return output
    output_file_folder = os.path.dirname(output_file)
    if output_file_folder and not os.path.exists(output_file_folder):
        os.makedirs(output_file_folder)
    with open(output_file, "w") as f_out:
        if output:
            f_out.write(json.dumps(output, indent=4))
    return None


def export_commands_meta(commands_meta, meta_output_path=None):
    options = jsbeautifier.default_options()
    options.indent_size = 4
    for key, module_info in commands_meta.items():
        file_name = "az_" + key + "_meta.json"
        if meta_output_path:
            file_name = meta_output_path + "/" + file_name
        file_folder = os.path.dirname(file_name)
        if file_folder and not os.path.exists(file_folder):
            os.makedirs(file_folder)
        with open(file_name, "w") as f_out:
            f_out.write(jsbeautifier.beautify(json.dumps(module_info), options))
