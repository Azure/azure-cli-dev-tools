# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
from azdev.operations.translator.utilities import AZDevTransNode


class AZDevTransNoWait(AZDevTransNode):
    DEFAULT_NO_WAIT_PARAM_DEST = 'no_wait'

    def __init__(self, no_wait_param):
        if not isinstance(no_wait_param, str):
            raise TypeError('no_wait_param a string, get "{}"'.format(no_wait_param))
        self.no_wait_param = no_wait_param

    def to_config(self, ctx):
        if self.no_wait_param == self.DEFAULT_NO_WAIT_PARAM_DEST:
            return 'support-no-wait', True
        else:
            return 'no-wait-param', self.no_wait_param


def build_command_no_wait(supports_no_wait, no_wait_param):
    if not no_wait_param:
        if supports_no_wait:
            no_wait_param = AZDevTransNoWait.DEFAULT_NO_WAIT_PARAM_DEST
    if not no_wait_param:
        return None
    return AZDevTransNoWait(no_wait_param)
