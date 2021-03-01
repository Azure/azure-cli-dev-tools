# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
from azure.cli.core.profiles import CustomResourceType


class AZRegisteredCustomResourceType(CustomResourceType):
    def __init__(self, register_name, import_prefix, client_name):
        self.register_name = register_name
        super(AZRegisteredCustomResourceType, self).__init__(import_prefix=import_prefix, client_name=client_name)


def register_custom_resource_type(register_name, import_prefix, client_name):
    return AZRegisteredCustomResourceType(register_name, import_prefix, client_name)
