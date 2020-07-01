# -----------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for
# license information.
# -----------------------------------------------------------------------------

import azdev.utilities.const as const
import os
import subprocess
import azdev.operations.extensions
from knack.util import CLIError
from azdev.utilities import display


def edit_activate(azure_config_path, dot_azure_config, dot_azdev_config):
    if const.IS_WINDOWS:
        ps1_edit(azure_config_path, dot_azure_config, dot_azdev_config)
        bat_edit(azure_config_path, dot_azure_config, dot_azdev_config)
    else:
        unix_edit(azure_config_path, dot_azure_config, dot_azdev_config)


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
    activate_path = os.path.join(azure_config_path, const.SCRIPTS,
                                 const.BAT_ACTIVATE)
    content = open(activate_path, "r").readlines()
    if const.AZ_CONFIG_DIR not in content[1]:
        content = content[0:1] + ['set ' + const.AZ_CONFIG_DIR +
                                  '=' + dot_azure_config + '\n',
                                  'set ' + const.AZ_AZDEV_DIR +
                                  '=' + dot_azdev_config] + content[1::]
        with open(activate_path, "w") as file:
            file.writelines(content)


def ps1_edit(azure_config_path, dot_azure_config, dot_azdev_config):
    activate_path = os.path.join(azure_config_path, const.SCRIPTS,
                                 const.ACTIVATE_PS)
    content = open(activate_path, "r").read()
    idx = content.find(const.PS1_VENV_SET)
    if idx < 0:
        raise RuntimeError("hmm, it looks like " + const.ACTIVATE_PS + " does"
                           " not set the virutal enviroment variable VIRTUAL_ENV")
    if content.find(const.EVN_AZ_CONFIG) < 0:
        content = content[:idx] + const.EVN_AZ_CONFIG + " = " + \
            "\"" + dot_azure_config + "\"; " + \
            const.EVN_AZ_DEV_CONFIG + " = " + \
            "\"" + dot_azdev_config + "\"; " + \
            content[idx:]
    with open(activate_path, "w") as file:
        file.write(content)


def install_cli(cli_path, venv_path):
    venv_path = os.environ[const.VIRTUAL_ENV] = venv_path
    src_path = os.path.join(cli_path, 'src')
    activate_path = os.path.join(venv_path, 'Scripts', 'activate') if const.IS_WINDOWS else 'source ' + os.path.join(
        venv_path, const.UN_BIN, const.UN_ACTIVATE)
    delimiter = ' && ' if const.IS_WINDOWS else '; '
    executable = None if const.IS_WINDOWS else const.BASH_EXE
    display("\nvenv activate path is " + str(activate_path))
    subprocess.check_call(activate_path + delimiter + 'pip install --ignore-installed azure-common', stdout=subprocess.DEVNULL,
                          stderr=subprocess.DEVNULL, shell=True, executable=executable)
    display("\nInstalling nspkg ")
    subprocess.check_call(activate_path + delimiter + const.PIP_E_CMD + os.path.join(src_path, 'azure-cli-nspkg'), stdout=subprocess.DEVNULL,
                          stderr=subprocess.DEVNULL, shell=True, executable=executable)
    display("\nInstalling telemetry ")
    subprocess.check_call(activate_path + delimiter + const.PIP_E_CMD + os.path.join(src_path, 'azure-cli-telemetry'),
                          stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, shell=True, executable=executable)
    display("\nInstalling core ")
    subprocess.check_call(activate_path + delimiter + const.PIP_E_CMD + os.path.join(src_path, 'azure-cli-core'),
                          stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, shell=True, executable=executable)
    display("\nInstalling cli ")
    subprocess.check_call(activate_path + delimiter + const.PIP_E_CMD + os.path.join(src_path, 'azure-cli'), shell=True, executable=executable)
    subprocess.check_call(activate_path + delimiter + const.PIP_E_CMD + os.path.join(src_path, 'azure-cli-testsdk'), stdout=subprocess.DEVNULL,
                          stderr=subprocess.DEVNULL, shell=True, executable=executable)


def install_extensions(venv_path, extensions):
    activate_path = os.path.join(venv_path, 'Scripts', 'activate') if const.IS_WINDOWS else 'source ' + os.path.join(
        venv_path, const.UN_BIN, const.UN_ACTIVATE)
    delimiter = ' && ' if const.IS_WINDOWS else '; '
    executable = None if const.IS_WINDOWS else const.BASH_EXE
    all_ext = azdev.operations.extensions.list_extensions()
    if extensions == ['*']:
        display("\nInstalling all extensions")
        for i in all_ext:
            subprocess.call(activate_path + delimiter + const.PIP_E_CMD + i['path'], shell=True, executable=executable)
        extensions = False
    else:
        display("\nInstalling the following extensions: " + str(extensions))
        extensions = set(extensions)
    k = 0
    while k < len(all_ext) and extensions:
        if all_ext[k]['name'] in extensions:
            subprocess.call(activate_path + delimiter + const.PIP_E_CMD + all_ext[k]['path'], shell=True, executable=executable)
            extensions.remove(all_ext[k]['name'])
        k += 1
    else:
        if extensions:
            raise CLIError("The following extensions were not found. Ensure you have added "
                           "the repo using `--repo/-r PATH`.\n    {}".format('\n    '.join(extensions)))
