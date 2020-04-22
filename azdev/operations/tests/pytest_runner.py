# -----------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for
# license information.
# -----------------------------------------------------------------------------

from knack.log import get_logger

from azdev.utilities import call


def get_test_runner(parallel, log_path, last_failed):
    """Create a pytest execution method"""
    def _run(test_paths, pytest_args):

        logger = get_logger(__name__)

        # arguments = ['-x', '-v', '--junit-xml', log_path]
        arguments = ['-x', '-v', '--boxed', '-p no:warnings', '--log-level=WARN']
        arguments.extend(test_paths)
        if parallel:
            arguments += ['-n', 'auto']
        if last_failed:
            arguments.append('--lf')
        if pytest_args:
            arguments += pytest_args
        cmd = 'python -m pytest {}'.format(' '.join(arguments))
        logger.info('Running: %s', cmd)
        return call(cmd)

    return _run
