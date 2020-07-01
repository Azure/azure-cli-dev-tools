# -----------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for
# license information.
# -----------------------------------------------------------------------------

from argparse import Action


class PerfBenchmarkCommandPrefixAction(Action):
    def __call__(self, parser, namespace, values, option_string=None):
        if not namespace.command_prefixes:
            namespace.command_prefixes = []

        namespace.command_prefixes.append(' '.join(values))
