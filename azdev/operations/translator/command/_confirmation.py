# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
from azdev.operations.translator.utilities import AZDevTransNode


class AZDevTransCommandConfirmation(AZDevTransNode):
    key = 'confirmation'

    def __init__(self, confirmation):
        self.confirmation = confirmation

    def to_config(self, ctx):
        raise NotImplementedError()


class AZDevTransCommandConfirmationBool(AZDevTransCommandConfirmation):

    def __init__(self, confirmation):
        if not isinstance(confirmation, bool):
            raise TypeError('Expect bool value, got "{}"'.format(confirmation))
        super(AZDevTransCommandConfirmationBool, self).__init__(confirmation)

    def to_config(self, ctx):
        return self.key, self.confirmation


class AZDevTransCommandConfirmationStr(AZDevTransCommandConfirmation):

    key = 'confirmation'

    def __init__(self, confirmation):
        if not isinstance(confirmation, str):
            raise TypeError('Expect str value, got "{}"'.format(confirmation))
        super(AZDevTransCommandConfirmationStr, self).__init__(confirmation)

    def to_config(self, ctx):
        return self.key, self.confirmation


def build_command_confirmation(confirmation):
    if not confirmation:
        return None

    if isinstance(confirmation, bool):
        return AZDevTransCommandConfirmationBool(confirmation)
    elif isinstance(confirmation, str):
        return AZDevTransCommandConfirmationStr(confirmation)
    else:
        # 'az extension add' ext_add_has_confirmed
        raise NotImplementedError()
