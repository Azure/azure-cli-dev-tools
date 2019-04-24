# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

def cf_{{ name }}(cli_ctx, *_):
{% if sdk_path %}
    from azure.cli.core.commands.client_factory import get_mgmt_service_client
    from {{ sdk_path }} import {{ sdk_client }}
    return get_mgmt_service_client(cli_ctx, {{ sdk_client }})
{% else %}
    from azure.cli.core.commands.client_factory import get_mgmt_service_client
    # TODO: Replace <PATH> and <CLIENT> and uncomment
    # from <PATH> import <CLIENT>
    # return get_mgmt_service_client(cli_ctx, <CLIENT>)
    return None
{% endif %}