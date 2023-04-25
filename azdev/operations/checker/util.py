# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------


import json
import os
import re
from enum import Enum

from knack.log import get_logger

logger = get_logger(__name__)

CMD_NAME_PATTERN = re.compile(r"\[\'commands\'\]\[\'([a-zA-Z0-9\-\s]+)\'\]")
CMD_PARAMETER_PROPERTY_PATTERN = re.compile(r"\[(.*?)\]")


class ChangeType(int, Enum):
    DEFAULT = 0
    ADD = 1
    CHANGE = 2
    REMOVE = 3


def extract_cmd_name(key):
    cmd_name_res = re.finditer(CMD_NAME_PATTERN, key)
    if not cmd_name_res:
        return False, None
    for cmd_match in cmd_name_res:
        cmd_name = cmd_match.group(1)
        return True, cmd_name


def extract_cmd_property(key, cmd_name):
    cmd_key_pattern = re.compile(cmd_name + r"\'\]\[\'([a-zA-Z0-9\-\_]+)\'\]")
    cmd_key_res = re.findall(cmd_key_pattern, key)
    if not cmd_key_res:
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
    output_file_folder = os.path.dirname(output_file)
    if not os.path.exists(output_file_folder):
        os.makedirs(output_file_folder)
    with open(output_file, "w") as f_out:
        f_out.write(json.dumps(output, indent=4))

if __name__ == '__main__':
    test_key = "root['sub_groups']['monitor']['sub_groups']['monitor private-link-scope']['sub_groups']['monitor private-link-scope scoped-resource']['commands']['monitor private-link-scope scoped-resource list']['is_preview']"
    test_key = "root['sub_groups']['monitor']['sub_groups']['monitor private-link-scope']['sub_groups']['monitor private-link-scope scoped-resource']['commands']['monitor private-link-scope scoped-resource list']['parameters'][0]['options'][1]"
    print(test_key)
    has_cmd, c_name = extract_cmd_name(test_key)
    print(has_cmd)
    print(c_name)
    has_cmd_key, cmd_key = extract_cmd_property(test_key, c_name)
    print(has_cmd_key)
    print(cmd_key)
    para_res = extract_para_info(test_key)
    print(para_res)