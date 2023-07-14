# -----------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for
# license information.
# -----------------------------------------------------------------------------

import json
import os
import re
import requests
import yaml

from knack.log import get_logger
from azdev.utilities.path import get_cli_repo_path

logger = get_logger(__name__)

try:
    with open(os.path.join(get_cli_repo_path(), 'scripts', 'ci', 'cmdcov.yml'), 'r') as file:
        config = yaml.safe_load(file)
# pylint: disable=broad-exception-caught
except Exception:
    url = "https://raw.githubusercontent.com/Azure/azure-cli/dev/scripts/ci/cmdcov.yml"
    response = requests.get(url)
    config = yaml.safe_load(response.text)
CMD_PATTERN = config['CMD_PATTERN']
QUO_PATTERN = config['QUO_PATTERN']
END_PATTERN = config['END_PATTERN']
DOCS_END_PATTERN = config['DOCS_END_PATTERN']
NOT_END_PATTERN = config['NOT_END_PATTERN']
NUMBER_SIGN_PATTERN = config['NUMBER_SIGN_PATTERN']


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


def search_argument_context(row_num, lines):
    cmds = []
    while row_num > 0:
        row_num -= 1
        # Match `with self.argument_context('') as c:`
        sub_pattern0 = r'with self.argument_context\(\'(.*?)\'[\),]'
        # Match `with self.argument_context(scope) as c:`
        sub_pattern1 = r'with self.argument_context\(scope[\),]'
        # Match `with self.argument_context(\'{} stop\'.format(scope)) as c:',
        sub_pattern2 = r'with self.argument_context\(\'(.*)\'.format\(scope\)\)'
        ref0 = re.findall(sub_pattern0, lines[row_num])
        ref1 = re.findall(sub_pattern1, lines[row_num])
        ref2 = re.findall(sub_pattern2, lines[row_num])
        # Match `with self.argument_context('') as c:`
        if ref0:
            cmds = ref0
            break
        # Match `with self.argument_context(scope) as c:`
        if ref1:
            sub_pattern = r'for scope in (.*):'
            cmds = json.loads(
                re.findall(sub_pattern, lines[row_num - 1])[0].replace('\'', '"'))
            break
        # Match `with self.argument_context(\'{} stop\'.format(scope)) as c:',
        if ref2:
            sub_pattern = r'for scope in (.*):'
            format_strings = json.loads(
                re.findall(sub_pattern, lines[row_num - 1])[0].replace('\'', '"'))
            for c in ref2:
                for f in format_strings:
                    cmds.append(c.replace('{}', f))
            break
    return cmds


def search_argument(line):
    params = []
    param_name = ''
    # Match ` + c.argument('xxx')?`
    pattern = r'\+\s+c.argument\((.*)\)?'
    ref = re.findall(pattern, line)
    if ref:
        # strip ' and \' and )
        param_name = ref[0].split(',')[0].strip(r"'\'\)")
        if 'options_list' in ref[0]:
            # Match ` options_list=xxx, or options_list=xxx)`
            sub_pattern = r'options_list=\[(.*?)\]'
            ref2 = re.findall(sub_pattern, ref[0])
            if ref2:
                params = ref2[0].replace('\'', '').replace('"', '').replace(' ', '').split(',')
        else:
            # if options_list not exist, generate by parameter name
            params = ['--' + param_name.replace('_', '-')]
    return params, param_name


def search_command_group(row_num, lines, command):
    cmd = ''
    while row_num > 0:
        row_num -= 1
        # Match `with self.command_group('local-context',` and `with self.command_group('xxx')`
        sub_pattern = r'with self.command_group\(\'(.*?)\',?'
        group = re.findall(sub_pattern, lines[row_num])
        if group:
            cmd = group[0] + ' ' + command
            break
    return cmd


def search_command(line):
    command = ''
    # Match `+ g.*command(xxx)`
    pattern = r'\+\s+g.(?:\w+)?command\((.*)\)'
    ref = re.findall(pattern, line)
    if ref:
        command = ref[0].split(',')[0].strip("'")
    return command
