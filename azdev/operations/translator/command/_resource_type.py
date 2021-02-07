# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
from azdev.operations.translator.utilities import AZDevTransNode


class AZDevTransBaseResourceType(AZDevTransNode):
    key = 'resource-type'

    def __init__(self, resource_type):
        self.resource_type = resource_type

    def to_config(self, ctx):
        raise NotImplementedError()


class AZDevTransResourceType(AZDevTransBaseResourceType):

    def __init__(self, resource_type):
        from azure.cli.core.profiles import ResourceType
        if not isinstance(resource_type, ResourceType):
            raise TypeError('Resource type is not an instant of "ResourceType", get "{}"'.format(
                type(resource_type)))
        super(AZDevTransResourceType, self).__init__(resource_type)
        self.name = resource_type.name

    def to_config(self, ctx):
        value = self.name
        return self.key, value


class AZDevTransCustomResourceType(AZDevTransBaseResourceType):

    def __init__(self, resource_type):
        from azure.cli.core.profiles import CustomResourceType
        if not isinstance(resource_type, CustomResourceType):
            raise TypeError('Resource type is not an instant of "ResourceType", get "{}"'.format(
                type(resource_type)))
        super(AZDevTransCustomResourceType, self).__init__(resource_type)

    def to_config(self, ctx):
        # TODO: add support for custom resource type
        raise NotImplementedError()


def build_command_resource_type(resource_type):
    if resource_type is None:
        return None
    from azure.cli.core.profiles import ResourceType, CustomResourceType, PROFILE_TYPE
    if resource_type != PROFILE_TYPE and not isinstance(resource_type, (ResourceType, CustomResourceType)):
        raise TypeError("Not supported resource_type type {}".format(type(resource_type)))

    if isinstance(resource_type, ResourceType):
        return AZDevTransResourceType(resource_type)
    elif isinstance(resource_type, CustomResourceType):
        # used for extensions. it will call register_resource_type.
        return AZDevTransCustomResourceType(resource_type)
    elif resource_type == PROFILE_TYPE:
        # used only in commands: ad sp | ad app | feature
        # TODO:
        raise NotImplementedError()
    else:
        raise NotImplementedError()
