# -----------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for
# license information.
# -----------------------------------------------------------------------------

import os
import sys
import subprocess
from knack.log import get_logger
from azdev.utilities import const, display


def get_test_runner(parallel, log_path, last_failed, no_exit_first, mark, clean):
    """Create a pytest execution method"""
    def _run(test_paths, pytest_args):

        logger = get_logger(__name__)

        if os.name == 'posix':
            arguments = ['-x', '-v', '--boxed', '-p no:warnings', '--log-level=WARN', '--junit-xml', log_path]
        else:
            arguments = ['-x', '-v', '-p no:warnings', '--log-level=WARN', '--junit-xml', log_path]

        if no_exit_first:
            arguments.remove('-x')

        if mark:
            arguments.append('-m "{}"'.format(mark))

        arguments.extend(test_paths)

        if parallel:
            arguments += ['-n', 'auto']
        if last_failed:
            arguments.append('--lf')
        if pytest_args:
            arguments += pytest_args
        cmd = 'python -m pytest {}'.format(' '.join(arguments))
        k = 0
        while k < len(test_paths):
            cmd = ("python " + ('-B ' if clean else '') +
                   "-m pytest {}").format(' '.join([test_paths[k]] + arguments))
            display("running cmd " + str(cmd))
            try:
                subprocess.check_call(cmd.split(), shell=const.IS_WINDOWS)
            except subprocess.CalledProcessError:
                if clean:
                    display("Test failed, cleaning up recordings")
                    recordings = os.path.join(test_paths[k], 'recordings')
                    if os.path.isdir(recordings):
                        recording_files = os.listdir(recordings)
                        for file in recording_files:
                            if file.endswith(".yaml"):
                                os.remove(os.path.join(recordings, file))
                sys.exit(1)
            logger.info('Running: %s', cmd)
            k += 1
        sys.exit(0)

    return _run
