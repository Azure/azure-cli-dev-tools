# -----------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for
# license information.
# -----------------------------------------------------------------------------


def get_test_runner(parallel, log_path):
    """Create a pytest execution method"""
    def _run(test_paths, pytest_args):
        from azdev.utilities import call
        from knack.log import get_logger

        def _linux_path(val):
            return val.replace('\\', '/')

        logger = get_logger(__name__)

        arguments = ['-p', 'no:warnings', '--no-print-logs', '--junit-xml', _linux_path(log_path)]
        arguments.extend([_linux_path(p) for p in test_paths])
        if parallel:
            arguments += ['-n', 'auto']
        if pytest_args:
            arguments += pytest_args
        cmd = 'pytest {}'.format(' '.join(arguments))
        logger.info('Running: {}'.format(cmd))
        return call(cmd)

    return _run
