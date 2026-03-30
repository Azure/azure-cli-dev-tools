# -----------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for
# license information.
# -----------------------------------------------------------------------------

import os
import sys

from knack.util import CLIError

from azdev.utilities import display, heading, py_cmd
from azdev.utilities.path import get_cli_repo_path


_LATEST_INDEX_SCRIPT = os.path.join('scripts', 'generate_latest_indices.py')


def _resolve_cli_repo_path(cli_path):
    if cli_path:
        resolved = os.path.abspath(os.path.expanduser(cli_path))
    else:
        resolved = get_cli_repo_path()

    if not resolved or resolved == '_NONE_':
        raise CLIError('Azure CLI repo path is not configured. Specify `--cli` or run `azdev setup`.')

    if not os.path.isdir(resolved):
        raise CLIError('Azure CLI repo path does not exist: {}'.format(resolved))

    return resolved


def _run_latest_index(mode, cli_path=None, profile='latest', all_profiles=False):
    if all_profiles:
        raise CLIError('`--all-profiles` is not supported yet. Use `--profile latest`.')

    if profile != 'latest':
        raise CLIError("Unsupported profile '{}'. Only `latest` is currently supported.".format(profile))

    repo_path = _resolve_cli_repo_path(cli_path)
    script_path = os.path.join(repo_path, _LATEST_INDEX_SCRIPT)
    if not os.path.isfile(script_path):
        raise CLIError('Unable to find azure-cli script: {}'.format(script_path))

    heading('Latest Index: {}'.format(mode.capitalize()))
    display('Azure CLI repo: {}'.format(repo_path))

    command = '{} {}'.format(_LATEST_INDEX_SCRIPT, mode)
    result = py_cmd(command, is_module=False, cwd=repo_path)

    output = result.result
    if isinstance(output, bytes):
        output = output.decode('utf-8', errors='replace')
    if output:
        output = output.replace(
            'python scripts/generate_latest_indices.py generate',
            'azdev latest-index generate'
        )
        display(output)

    if result.exit_code:
        sys.exit(result.exit_code)


def generate_latest_index(cli_path=None, profile='latest', all_profiles=False):
    _run_latest_index('generate', cli_path=cli_path, profile=profile, all_profiles=all_profiles)


def verify_latest_index(cli_path=None, profile='latest', all_profiles=False):
    _run_latest_index('verify', cli_path=cli_path, profile=profile, all_profiles=all_profiles)
