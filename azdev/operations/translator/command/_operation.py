# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
from collections import OrderedDict
from azdev.operations.translator.utilities import AZDevTransNode


class AZDevTransBaseCommandOperation(AZDevTransNode):
    key = 'operation'

    def __init__(self, command_operation):
        self.command_operation = command_operation

    def to_config(self, ctx):
        raise NotImplementedError()


class AZDevTransCommandOperation(AZDevTransBaseCommandOperation):

    def __init__(self, command_operation):
        from azure.cli.core.commands.command_operation import CommandOperation
        if not isinstance(command_operation, CommandOperation):
            raise TypeError('Command operation is not an instant of "CommandOperation", get "{}"'.format(
                type(command_operation)))
        super(AZDevTransCommandOperation, self).__init__(command_operation)
        self.operation = command_operation.operation

    def to_config(self, ctx):
        value = ctx.get_operation_import_path(self.operation)
        return self.key, value


class AZDevTransWaitCommandOperation(AZDevTransBaseCommandOperation):
    key = 'wait-operation'

    def __init__(self, command_operation):
        from azure.cli.core.commands.command_operation import WaitCommandOperation
        if not isinstance(command_operation, WaitCommandOperation):
            raise TypeError('Command operation is not an instant of "WaitCommandOperation", get "{}"'.format(
                type(command_operation)))
        super(AZDevTransWaitCommandOperation, self).__init__(command_operation)
        self.operation = command_operation.operation

    def to_config(self, ctx):
        value = ctx.get_operation_import_path(self.operation)
        return self.key, value


class AZDevTransShowCommandOperation(AZDevTransBaseCommandOperation):
    key = 'show-operation'

    def __init__(self, command_operation):
        from azure.cli.core.commands.command_operation import ShowCommandOperation
        if not isinstance(command_operation, ShowCommandOperation):
            raise TypeError('Command operation is not an instant of "ShowCommandOperation", get "{}"'.format(
                type(command_operation)))
        super(AZDevTransShowCommandOperation, self).__init__(command_operation)
        self.operation = command_operation.operation

    def to_config(self, ctx):
        value = ctx.get_operation_import_path(self.operation)
        return self.key, value


class AZDevTransGenericUpdateCommandOperation(AZDevTransBaseCommandOperation):
    key = 'generic-update'

    def __init__(self, command_operation):
        from azure.cli.core.commands.command_operation import GenericUpdateCommandOperation
        if not isinstance(command_operation, GenericUpdateCommandOperation):
            raise TypeError('Command operation is not an instant of "GenericUpdateCommandOperation", get "{}"'.format(
                type(command_operation)))
        super(AZDevTransGenericUpdateCommandOperation, self).__init__(command_operation)
        self.getter_operation = command_operation.getter_operation
        self.setter_operation = command_operation.setter_operation
        self.setter_arg_name = command_operation.setter_arg_name
        self.custom_function_operation = command_operation.custom_function_operation
        self.child_collection_prop_name = command_operation.child_collection_prop_name
        self.child_collection_key = command_operation.child_collection_key
        self.child_arg_name = command_operation.child_arg_name

    def to_config(self, ctx):
        value = OrderedDict()
        value['getter-operation'] = ctx.get_operation_import_path(self.getter_operation)
        value['setter-operation'] = ctx.get_operation_import_path(self.setter_operation)
        value['setter-arg-name'] = self.setter_arg_name
        if self.custom_function_operation:
            value['custom-function-operation'] = ctx.get_operation_import_path(self.custom_function_operation)
        if self.child_collection_prop_name:
            child_value = OrderedDict()
            child_value['collection-prop-name'] = self.child_collection_prop_name
            child_value['collection-key'] = self.child_collection_key
            child_value['arg-name'] = self.child_arg_name
            value['child'] = child_value
        return self.key, value


def build_command_operation(command_operation):
    from azure.cli.core.commands.command_operation import BaseCommandOperation, CommandOperation, WaitCommandOperation,\
        ShowCommandOperation, GenericUpdateCommandOperation
    if command_operation is None:
        return None
    if not isinstance(command_operation, BaseCommandOperation):
        raise TypeError('Command operation is not an instant of "BaseCommandOperation", get "{}"'.format(
                type(command_operation)))
    if isinstance(command_operation, CommandOperation):
        return AZDevTransCommandOperation(command_operation)
    elif isinstance(command_operation, WaitCommandOperation):
        return AZDevTransWaitCommandOperation(command_operation)
    elif isinstance(command_operation, ShowCommandOperation):
        return AZDevTransShowCommandOperation(command_operation)
    elif isinstance(command_operation, GenericUpdateCommandOperation):
        return AZDevTransGenericUpdateCommandOperation(command_operation)
    else:
        raise NotImplementedError()