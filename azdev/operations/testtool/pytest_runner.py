# -----------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for
# license information.
# -----------------------------------------------------------------------------

import os
import subprocess
from azdev.utilities import const, display
import multiprocessing


def get_test_runner(parallel, log_path, last_failed, no_exit_first, mark, clean):
    """Create a pytest execution method"""
    def _run(test_paths, pytest_args):

        if os.name == 'posix':
            arguments = ['-x', '-v', '--boxed', '-p no:warnings', '--log-level=WARN', '--junit-xml', log_path]
        else:
            arguments = ['-x', '-v', '-p no:warnings', '--log-level=WARN', '--junit-xml', log_path]

        if no_exit_first:
            arguments.remove('-x')

        if mark:
            arguments.append('-m "{}"'.format(mark))

        if parallel:
            arguments += ['-n', 'auto']
        if last_failed:
            arguments.append('--lf')
        if pytest_args:
            arguments += pytest_args
        tests_params = [(i, clean, arguments) for i in test_paths]
        test_pass = True
        with multiprocessing.Pool(multiprocessing.cpu_count()) as the_pool:
            try:
                the_pool.map(_run_test, tests_params)
            except subprocess.CalledProcessError:
                test_pass = False
        return test_pass

    return _run


def _run_test(test_args):
    cmd = ("python " + ('-B ' if test_args[1] else ' ') +
           "-m pytest {}").format(' '.join([test_args[0]] + test_args[2]))
    try:
        subprocess.check_call(cmd.split(), shell=const.IS_WINDOWS)
    except subprocess.CalledProcessError as e:
        if test_args[1]:
            display("Test failed, cleaning up recordings")
            recordings = os.path.join(test_args[0], 'recordings')
            if os.path.isdir(recordings):
                recording_files = os.listdir(recordings)
                for file in recording_files:
                    if file.endswith(".yaml"):
                        os.remove(os.path.join(recordings, file))
        raise e
