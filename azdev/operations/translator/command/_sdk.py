# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
from azdev.operations.translator.utilities import AZDevTransNode
from collections import OrderedDict


class AZDevTransBaseSDK(AZDevTransNode):
    key = 'sdk'

    def __init__(self, resource_type, operation_group):
        self.resource_type = resource_type
        self.operation_group = operation_group

    def to_config(self, ctx):
        raise NotImplementedError()

    def __hash__(self):
        return hash((self.resource_type.import_prefix, self.resource_type.client_name, self.operation_group))

    def __eq__(self, other):
        return isinstance(other, AZDevTransBaseSDK) and \
               self.resource_type.import_prefix == other.resource_type.import_prefix and \
               self.resource_type.client_name == other.resource_type.client_name and \
               self.operation_group == other.operation_group

    def __ne__(self, other):
        return not(self == other)


class AZDevTransSDK(AZDevTransBaseSDK):

    def __init__(self, resource_type, operation_group):
        from azure.cli.core.profiles import ResourceType
        if not isinstance(resource_type, ResourceType):
            raise TypeError('Resource type is not an instant of "ResourceType", get "{}"'.format(
                type(resource_type)))
        super(AZDevTransSDK, self).__init__(resource_type, operation_group)
        self.name = resource_type.name
        self.import_prefix = resource_type.import_prefix
        self.client_name = resource_type.client_name

    def to_config(self, ctx):
        value = OrderedDict()
        value['resource-type'] = self.name
        if self.operation_group:
            value['operation-group'] = self.operation_group
        if ctx.is_multi_api_sdk(self.resource_type):
            value['api-version'] = ctx.get_api_version(self.resource_type, self.operation_group)
        return self.key, value


class AZDevTransVendorSDK(AZDevTransBaseSDK):

    def __init__(self, resource_type, operation_group):
        from azure.cli.core.profiles import CustomResourceType
        if not isinstance(resource_type, CustomResourceType):
            raise TypeError('Resource type is not an instant of "ResourceType", get "{}"'.format(
                type(resource_type)))
        super(AZDevTransVendorSDK, self).__init__(resource_type, operation_group)
        self.import_prefix = resource_type.import_prefix
        self.client_name = resource_type.client_name

    def to_config(self, ctx):
        value = OrderedDict()
        value['import-prefix'] = self.import_prefix
        value['client-name'] = self.client_name
        if self.operation_group:
            value['operation-group'] = self.operation_group
        return self.key, value


def build_command_sdk(resource_type, operation_group):
    from azure.cli.core.profiles import ResourceType, CustomResourceType, PROFILE_TYPE

    if resource_type is None:
        return None
    if operation_group is not None and not isinstance(operation_group, str):
        raise ValueError("Expect None or sting for operation group, Got '{}'".format(operation_group))
    if resource_type != PROFILE_TYPE and not isinstance(resource_type, (ResourceType, CustomResourceType)):
        raise TypeError("Not supported resource_type type {}".format(type(resource_type)))

    if isinstance(resource_type, ResourceType):
        return AZDevTransSDK(resource_type, operation_group)
    elif isinstance(resource_type, CustomResourceType):
        # used for extensions. it will call register_resource_type.
        return AZDevTransVendorSDK(resource_type, operation_group)
    elif resource_type == PROFILE_TYPE:
        # TODO: used in commands: ad sp | ad app | feature
        raise NotImplementedError()
    else:
        raise NotImplementedError()
