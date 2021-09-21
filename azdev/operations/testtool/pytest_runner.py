# -----------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for
# license information.
# -----------------------------------------------------------------------------

import os

from knack.log import get_logger

from azdev.utilities import call, get_cli_repo_path


def get_test_runner(parallel, log_path, last_failed, no_exit_first, mark, coverage=False, no_htmlcov=False, append_coverage=False, coverage_path=None):
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

        if coverage:
            if coverage_path is None:
                path = get_cli_repo_path()
            else:
                path = coverage_path
            arguments.append("--cov=\"{}\"".format(path))
            
            if append_coverage:
                arguments.append("--cov-append")

        cmd = 'pytest {}'.format(' '.join(arguments))

        if coverage and not no_htmlcov:
            cmd = "{} ; {}".format(cmd, "coverage html") 

        logger.info('Running: %s', cmd)
        return call(cmd)

    return _run
