# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

import json
import os
import re
from enum import Enum
import jsbeautifier
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


def add_to_command_tree(tree, key, value):
    parts = key.split()
    subtree = tree
    for part in parts[:-1]:
        if not subtree.get(part):
            subtree[part] = {}
        subtree = subtree[part]
    subtree[parts[-1]] = value


def dump_command_tree(command_tree, output_file):
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(command_tree, f, indent=4)
