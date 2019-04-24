# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

# pylint: disable=line-too-long
from azure.cli.core.commands import CliCommandType
from {{ mod_path }}._client_factory import cf_{{ name }}


def load_command_table(self, _):
{% if sdk_path %}
    {{ name }}_sdk = CliCommandType(
        operations_tmpl='{{ sdk_path }}.operations#{{ display_name }}Operations.{}',
        client_factory=cf_{{ name }})
{% else %}
    {{ name }}_sdk = CliCommandType(
        operations_tmpl='{{ sdk_path }}.operations#{{ display_name }}Operations.{}',
        client_factory=cf_{{ name }})
{% endif %}

    with self.command_group('{{ name }}', {{ name }}_sdk, client_factory=cf_{{ name }}) as g:
        g.custom_command('create', 'create_{{ name }}')
        g.command('delete', 'delete')
        g.custom_command('list', 'list_{{ name }}')
        g.show_command('show', 'get')
        g.generic_update_command('update', setter_name='update', custom_func_name='update_{{ name }}')

