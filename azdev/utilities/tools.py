# -----------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for
# license information.
# -----------------------------------------------------------------------------

from knack.util import CLIError


def require_virtual_env():
    import os
    from azdev.utilities import ENV_VAR_VIRTUAL_ENV

    env = os.getenv(ENV_VAR_VIRTUAL_ENV)
    if not env:
        raise CLIError('This command can only be run from an active virtual environment.')


def require_azure_cli():
    try:
        import azure.cli.core  # pylint: disable=unused-variable
    except ImportError:
        raise CLIError('CLI is not installed. Run `azdev setup`.')
