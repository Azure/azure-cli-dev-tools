# -----------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for
# license information.
# -----------------------------------------------------------------------------

import os
import subprocess
import sys

from knack.log import get_logger
from knack.util import CommandResultItem

from .const import ENV_VAR_VIRTUAL_ENV, IS_WINDOWS
from .display import display


logger = get_logger(__name__)


def call(command, **kwargs):
    """ Run an arbitrary command but don't buffer the output.

    :param command: The entire command line to run.
    :param kwargs: Any kwargs supported by subprocess.Popen
    :returns: (int) process exit code.
    """
    return subprocess.call(
        command.split(),
        shell=IS_WINDOWS,
        **kwargs)


def cmd(command, message=False, show_stderr=True, **kwargs):
    """ Run an arbitrary command.

    :param command: The entire command line to run.
    :param message: A custom message to display, or True (bool) to use a default.
    :param show_stderr: On error, display the contents of STDERR.
    :param kwargs: Any kwargs supported by subprocess.Popen
    :returns: CommandResultItem object.
    """
    # use default message if custom not provided
    if message == True:
        message = 'Running: {}\n'.format(command)

    if message:
        display(message)

    try:
        output = subprocess.check_output(
            command.split(),
            stderr=subprocess.STDOUT if show_stderr else None,
            shell=IS_WINDOWS,
            **kwargs).decode('utf-8').strip()
        return CommandResultItem(output, exit_code=0, error=None)
    except subprocess.CalledProcessError as err:
        return CommandResultItem(err.output, exit_code=err.returncode, error=err)


def py_cmd(command, message=False, show_stderr=True, **kwargs):
    """ Run a script or command with Python.

    :param command: The arguments to run python with.
    :param message: A custom message to display, or True (bool) to use a default.
    :param show_stderr: On error, display the contents of STDERR.
    :param kwargs: Any kwargs supported by subprocess.Popen
    :returns: CommandResultItem object.
    """
    env_path = os.environ.get(ENV_VAR_VIRTUAL_ENV, None)
    python_bin = sys.executable if not env_path else os.path.join(env_path, 'Scripts' if sys.platform == 'win32' else 'bin', 'python')
    command = '{} -m {}'.format(python_bin, command)
    return cmd(command, message, show_stderr, **kwargs)


def pip_cmd(command, message=False, show_stderr=True, **kwargs):
    """ Run a pip command.

    :param command: The arguments to run pip with.
    :param message: A custom message to display, or True (bool) to use a default.
    :param show_stderr: On error, display the contents of STDERR.
    :param kwargs: Any kwargs supported by subprocess.Popen
    :returns: CommandResultItem object.
    """
    command = 'pip {}'.format(command)
    return py_cmd(command, message, show_stderr, **kwargs)
