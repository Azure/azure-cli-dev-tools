# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
from azdev.operations.translator.utilities import AZDevTransNode


class AZDevCommandConfirmation(AZDevTransNode):
    key = 'confirmation'

    def __init__(self, confirmation):
        self.confirmation = confirmation

    def to_config(self, ctx):
        raise NotImplementedError()


class AZDevBoolCommandConfirmation(AZDevCommandConfirmation):

    def __init__(self, confirmation):
        if not isinstance(confirmation, bool):
            raise TypeError('Expect bool value, got "{}"'.format(confirmation))
        super(AZDevBoolCommandConfirmation, self).__init__(confirmation)

    def to_config(self, ctx):
        return self.key, self.confirmation


class AZDevStrCommandConfirmation(AZDevCommandConfirmation):

    key = 'confirmation'

    def __init__(self, confirmation):
        if not isinstance(confirmation, str):
            raise TypeError('Expect str value, got "{}"'.format(confirmation))
        super(AZDevStrCommandConfirmation, self).__init__(confirmation)

    def to_config(self, ctx):
        return self.key, self.confirmation


def build_command_confirmation(confirmation):
    if not confirmation:
        return None

    if isinstance(confirmation, bool):
        return AZDevBoolCommandConfirmation(confirmation)
    elif isinstance(confirmation, str):
        return AZDevStrCommandConfirmation(confirmation)
    else:
        # 'az extension add' ext_add_has_confirmed
        raise NotImplementedError()
