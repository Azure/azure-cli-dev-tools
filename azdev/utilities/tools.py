# -----------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for
# license information.
# -----------------------------------------------------------------------------

from knack.util import CLIError
from . import const
import os


def require_virtual_env():
    from azdev.utilities import get_env_path

    env = get_env_path()
    if not env:
        raise CLIError('This command can only be run from an active virtual environment.')
    if not os.environ.get(const.AZ_CONFIG_DIR):
        raise CLIError(
            "AZURE_CONFIG_DIR env var is not set. Please run 'azdev setup'")
    if not os.path.exists(os.path.join(os.environ[const.AZ_CONFIG_DIR], "config")):
        raise CLIError(
            "The Azure config file does not exist. Please run 'azdev setup'")


def require_azure_cli():
    try:
        import azure.cli.core  # pylint: disable=unused-import, unused-variable
    except ImportError:
        raise CLIError('CLI is not installed. Run `azdev setup`.')
