# -----------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for
# license information.
# -----------------------------------------------------------------------------

import re
from azdev.operations.constant import (
    CMD_PATTERN, QUO_PATTERN, END_PATTERN, DOCS_END_PATTERN, NOT_END_PATTERN, NUMBER_SIGN_PATTERN)

def get_all_tested_commands_from_regex(lines):
    """
    get all tested commands from test_*.py
    """
    # pylint: disable=too-many-nested-blocks
    ref = []
    total_lines = len(lines)
    row_num = 0
    count = 1
    while row_num < total_lines:
        re_idx = None
        if re.findall(NUMBER_SIGN_PATTERN, lines[row_num]):
            row_num += 1
            continue
        if re.findall(CMD_PATTERN[0], lines[row_num]):
            re_idx = 0
        if re_idx is None and re.findall(CMD_PATTERN[1], lines[row_num]):
            re_idx = 1
        if re_idx is None and re.findall(CMD_PATTERN[2], lines[row_num]):
            re_idx = 2
        if re_idx is None and re.findall(CMD_PATTERN[3], lines[row_num]):
            re_idx = 3
        if re_idx is not None:
            command = re.findall(CMD_PATTERN[re_idx], lines[row_num])[0]
            while row_num < total_lines:
                if (re_idx in [0, 1] and not re.findall(END_PATTERN, lines[row_num])) or \
                        (re_idx == 2 and (row_num + 1) < total_lines and
                         re.findall(NOT_END_PATTERN, lines[row_num + 1])):
                    row_num += 1
                    cmd = re.findall(QUO_PATTERN, lines[row_num])
                    if cmd:
                        command += cmd[0][1]
                elif re_idx == 3 and (row_num + 1) < total_lines \
                        and not re.findall(DOCS_END_PATTERN, lines[row_num]):
                    row_num += 1
                    command += lines[row_num][:-1]
                else:
                    command = command + ' ' + str(count)
                    ref.append(command)
                    row_num += 1
                    count += 1
                    break
            else:
                command = command + ' ' + str(count)
                ref.append(command)
                row_num += 1
                count += 1
                break
        else:
            row_num += 1
    return ref
