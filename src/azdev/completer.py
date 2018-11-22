# -----------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for
# license information.
# -----------------------------------------------------------------------------

from azure.cli.core.decorators import Completer


@Completer
def get_test_completion(cmd, prefix, namespace, **kwargs):  # pylint: disable=unused-argument
    # TODO: return the list of keys from the index
    return ['storage', 'network', 'redis']

