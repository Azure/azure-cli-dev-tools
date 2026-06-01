# -----------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for
# license information.
# -----------------------------------------------------------------------------

import os
import subprocess
import sys
import shlex

from knack.log import get_logger
from knack.util import CommandResultItem

logger = get_logger(__name__)


def quote_arg(arg):
    """ Quote a single command-line argument so it survives the shell/argv parsing
    performed by the command runners in this module.

    On Windows, command strings are passed verbatim to ``subprocess`` (and ultimately
    ``CreateProcess``), so Windows-style quoting via ``subprocess.list2cmdline`` is used.
    On POSIX, command strings are split with ``shlex.split``, so POSIX-style quoting via
    ``shlex.quote`` is used. This makes paths containing spaces (e.g. OneDrive folders)
    safe to interpolate into command strings.

    :param arg: The argument to quote.
    :returns: (str) the quoted argument.
    """
    from azdev.utilities import IS_WINDOWS
    arg = str(arg)
    if IS_WINDOWS:
        return subprocess.list2cmdline([arg])
    return shlex.quote(arg)


class CommandError(Exception):

    def __init__(self, output, exit_code, command):
        message = "Command `{}` failed with exit code {}:\n{}".format(command, exit_code, output)
        self.exit_code = exit_code
        self.output = output
        self.command = command
        super().__init__(message)


def call(command, **kwargs):
    """ Run an arbitrary command but don't buffer the output.

    :param command: The entire command line to run.
    :param kwargs: Any kwargs supported by subprocess.Popen
    :returns: (int) process exit code.
    """
    from azdev.utilities import IS_WINDOWS
    cmd_args = command
    if IS_WINDOWS and command.startswith('az '):
        cmd_args = "az.bat " + command[3:]
    if not IS_WINDOWS:
        cmd_args = shlex.split(command)
    return subprocess.run(
        cmd_args,
        check=False,  # supress subprocess-run-check linter warning, no CalledProcessError
        **kwargs).returncode


def cmd(command, message=False, show_stderr=True, raise_error=False, **kwargs):
    """ Run an arbitrary command.

    :param command: The entire command line to run.
    :param message: A custom message to display, or True (bool) to use a default.
    :param show_stderr: On error, display the contents of STDERR.
    :param raise_error: On error, raise CommandError.
    :param kwargs: Any kwargs supported by subprocess.Popen
    :returns: CommandResultItem object.
    """
    from azdev.utilities import IS_WINDOWS, display

    # use default message if custom not provided
    if message is True:
        message = 'Running: {}\n'.format(command)

    if message:
        display(message)

    logger.info("Running: %s", command)
    cmd_args = command
    if IS_WINDOWS and command.startswith('az '):
        cmd_args = "az.bat " + command[3:]
    if not IS_WINDOWS:
        cmd_args = shlex.split(command)
    try:
        output = subprocess.run(
            cmd_args,
            check=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT if show_stderr else None,
            **kwargs).stdout.decode('utf-8').strip()
        logger.debug(output)
        return CommandResultItem(output, exit_code=0, error=None)
    except subprocess.CalledProcessError as err:
        if raise_error:
            raise CommandError(err.output.decode(), err.returncode, command)
        return CommandResultItem(err.output, exit_code=err.returncode, error=err)


def py_cmd(command, message=False, show_stderr=True, raise_error=False, is_module=True, **kwargs):
    """ Run a script or command with Python.

    :param command: The arguments to run python with.
    :param message: A custom message to display, or True (bool) to use a default.
    :param show_stderr: On error, display the contents of STDERR.
    :param raise_error: On error, raise CommandError.
    :param is_module: Run a Python module as a script with -m.
    :param kwargs: Any kwargs supported by subprocess.Popen
    :returns: CommandResultItem object.
    """
    from azdev.utilities import get_env_path
    env_path = get_env_path()
    python_bin = sys.executable if not env_path else os.path.join(
        env_path, 'Scripts' if sys.platform == 'win32' else 'bin', 'python')
    if is_module:
        command = '{} -m {}'.format(python_bin, command)
    else:
        command = '{} {}'.format(python_bin, command)
    return cmd(command, message, show_stderr, raise_error, **kwargs)


def pip_cmd(command, message=False, show_stderr=True, raise_error=True, **kwargs):
    """ Run a pip command.

    :param command: The arguments to run pip with.
    :param message: A custom message to display, or True (bool) to use a default.
    :param show_stderr: On error, display the contents of STDERR.
    :param raise_error: On error, raise CommandError. As pip_cmd is usually called as a control function, instead of
      a test target, default to True.
    :param kwargs: Any kwargs supported by subprocess.Popen
    :returns: CommandResultItem object.
    """
    command = 'pip {}'.format(command)
    return py_cmd(command, message, show_stderr, raise_error, **kwargs)
