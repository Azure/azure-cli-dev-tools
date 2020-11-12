# -----------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for
# license information.
# -----------------------------------------------------------------------------

import os
import subprocess
import platform
from knack.util import CLIError
import azdev.operations.extensions
from azdev.utilities import display, shell_cmd
from . import const


def edit_activate(azure_config_path, dot_azure_config, dot_azdev_config):
    if const.IS_WINDOWS:
        ps1_edit(azure_config_path, dot_azure_config, dot_azdev_config)
        bat_edit(azure_config_path, dot_azure_config, dot_azdev_config)
    else:
        unix_edit(azure_config_path, dot_azure_config, dot_azdev_config)


def edit_pyenv_activate(activate_path):
    set_azdev_content = 'set -gx AZDEV_CONFIG_DIR "${prefix}/.azdev";\n'
    set_azure_content = 'set -gx AZURE_CONFIG_DIR "${prefix}/.azure";\n'
    export_azdev_content = 'export AZDEV_CONFIG_DIR="${prefix}/.azdev";\n'
    export_azure_content = 'export AZURE_CONFIG_DIR="${prefix}/.azure";\n'

    insert(activate_path, set_azdev_content, get_line_num(activate_path, "set -gx VIRTUAL_ENV \"${prefix}\";"))
    insert(activate_path, set_azure_content, get_line_num(activate_path, "set -gx VIRTUAL_ENV \"${prefix}\";"))
    insert(activate_path, export_azdev_content, get_line_num(activate_path, "export VIRTUAL_ENV=\"${prefix}\";"))
    insert(activate_path, export_azure_content, get_line_num(activate_path, "export VIRTUAL_ENV=\"${prefix}\";"))


def insert(file_path, content, line_num):
    if line_num == -1:
        raise CLIError("Cannot find a proper place to set/export environment variable.")
    if get_line_num(file_path, content) == -1:
        with open(file_path, 'r+') as reader:
            file_content = reader.readlines()
            file_content.insert(line_num, content)
            reader.seek(0)
            reader.writelines(file_content)


def get_line_num(file_path, target):
    with open(file_path, 'r') as reader:
        for num, line in enumerate(reader, 1):
            if target in line:
                return num
    return -1


def unix_edit(azure_config_path, dot_azure_config, dot_azdev_config):
    activate_path = os.path.join(azure_config_path, const.UN_BIN,
                                 const.UN_ACTIVATE)
    content = open(activate_path, "r").readlines()

    # check if already ran setup before
    if const.AZ_CONFIG_DIR not in content[0]:
        content = [const.AZ_CONFIG_DIR + '=' + dot_azure_config + '\n',
                   const.UN_EXPORT + ' ' + const.AZ_CONFIG_DIR + '\n',
                   const.AZ_AZDEV_DIR + '=' + dot_azdev_config + '\n',
                   const.UN_EXPORT + ' ' + const.AZ_AZDEV_DIR + '\n'] + content
        with open(activate_path, "w") as file:
            file.writelines(content)


def bat_edit(azure_config_path, dot_azure_config, dot_azdev_config):
    activate_path = os.path.join(azure_config_path, 'Scripts',
                                 'activate.bat')
    content = open(activate_path, "r").readlines()
    if const.AZ_CONFIG_DIR not in content[1]:
        content = content[0:1] + ['set ' + const.AZ_CONFIG_DIR +
                                  '=' + dot_azure_config + '\n',
                                  'set ' + const.AZ_AZDEV_DIR +
                                  '=' + dot_azdev_config] + content[1::]
        with open(activate_path, "w") as file:
            file.writelines(content)


def ps1_edit(azure_config_path, dot_azure_config, dot_azdev_config):
    activate_path = os.path.join(azure_config_path, 'Scripts',
                                 'Activate.ps1')
    content = open(activate_path, "r").read()
    idx = content.find('$env:VIRTUAL_ENV')
    if idx < 0:
        raise CLIError("hmm, it looks like Activate.ps1 does"
                       " not set the virutal enviroment variable VIRTUAL_ENV")
    if content.find('$env:AZURE_CONFIG_DIR') < 0:
        content = content[:idx] + '$env:AZURE_CONFIG_DIR' + " = " + \
            "\"" + dot_azure_config + "\"; " + \
            "$env:AZDEV_CONFIG_DIR = " + \
            "\"" + dot_azdev_config + "\"; " + \
            content[idx:]
    with open(activate_path, "w") as file:
        file.write(content)


def install_cli(cli_path, venv_path):
    src_path = os.path.join(cli_path, 'src')
    activate_path = (os.path.join(venv_path, 'Scripts', 'activate')
                     if const.IS_WINDOWS else 'source ' + os.path.join(venv_path, const.UN_BIN, const.UN_ACTIVATE))
    delimiter = ' && ' if const.IS_WINDOWS else '; '
    executable = None if const.IS_WINDOWS else '/bin/bash'
    display("\nvenv activate path is " + str(activate_path))
    shell_cmd(activate_path + delimiter + 'pip install --ignore-installed azure-common',
              stdout=subprocess.DEVNULL,
              stderr=subprocess.DEVNULL, raise_ex=False, executable=executable)
    display("\nInstalling telemetry ")
    shell_cmd(activate_path + delimiter + const.PIP_E_CMD + os.path.join(src_path, 'azure-cli-telemetry'),
              stdout=subprocess.DEVNULL, raise_ex=False, stderr=subprocess.DEVNULL, executable=executable)
    display("\nInstalling core ")
    shell_cmd(activate_path + delimiter + const.PIP_E_CMD + os.path.join(src_path, 'azure-cli-core'),
              stdout=subprocess.DEVNULL, raise_ex=False, stderr=subprocess.DEVNULL, executable=executable)
    shell_cmd(activate_path + delimiter + const.PIP_E_CMD + os.path.join(src_path, 'azure-cli-testsdk'),
              stdout=subprocess.DEVNULL,
              stderr=subprocess.DEVNULL, raise_ex=False, executable=executable)
    display("\nInstalling cli ")
    shell_cmd(activate_path + delimiter + const.PIP_E_CMD + os.path.join(src_path, 'azure-cli'),
              raise_ex=False, executable=executable)
    req_file = 'requirements.py3.{}.txt'.format(platform.system().lower() if const.IS_WINDOWS else platform.system())
    req_file = "{}/src/azure-cli/{}".format(cli_path, req_file)
    display("Installing " + req_file)
    shell_cmd(activate_path + delimiter + const.PIP_R_CMD + req_file, raise_ex=False, executable=executable)


def install_extensions(venv_path, extensions):
    activate_path = os.path.join(venv_path, 'Scripts', 'activate') if const.IS_WINDOWS else 'source ' + os.path.join(
        venv_path, const.UN_BIN, const.UN_ACTIVATE)
    delimiter = ' && ' if const.IS_WINDOWS else '; '
    executable = None if const.IS_WINDOWS else '/bin/bash'
    all_ext = azdev.operations.extensions.list_extensions()
    if extensions == ['*']:
        display("\nInstalling all extensions")
        for i in all_ext:
            shell_cmd(activate_path + delimiter + const.PIP_E_CMD + i['path'], executable=executable)
        extensions = False
    else:
        display("\nInstalling the following extensions: " + str(extensions))
        extensions = set(extensions)
    k = 0
    while k < len(all_ext) and extensions:
        if all_ext[k]['name'] in extensions:
            shell_cmd(activate_path + delimiter + const.PIP_E_CMD + all_ext[k]['path'],
                      executable=executable)
            extensions.remove(all_ext[k]['name'])
        k += 1
    if extensions:
        raise CLIError("The following extensions were not found. Ensure you have added "
                       "the repo using `--repo/-r PATH`.\n    {}".format('\n    '.join(extensions)))
