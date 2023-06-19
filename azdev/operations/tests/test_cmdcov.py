# -----------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for
# license information.
# -----------------------------------------------------------------------------


from pprint import pprint
from azdev.operations.regex import (
    get_all_tested_commands_from_regex,
    search_argument,
    search_argument_context,
    search_command,
    search_command_group)


# pylint: disable=line-too-long
# one line test
def test_one_line_regex():
    lines = [
        # start with self.cmd.
        'self.cmd(\'image builder create -n {tmpl_02} -g {rg} --identity {ide} --scripts {script} --image-source {img_src} --build-timeout 22\')\n',
        # start with blanks, match self.cmd("").
        '            self.cmd("role assignment create --assignee {assignee} --role {role} --scope {scope}")\n',
        # start with blanks, match self.cmd('').
        '            self.cmd(\'role assignment create --assignee {assignee} --role {role} --scope {scope}\')\n',
        # start with multiple blanks, characters, self.cmd
        '     identity_id = self.cmd(\'identity create -g {rg} -n {ide}\').get_output_in_json()[\'clientId\']\n',
        # start with blanks, match self.cmd, use fstring, ''
        '        self.cmd(f\'afd profile usage -g {resource_group} --profile-name {profile_name}\', checks=usage_checks)',
        # start with blanks, match self.cmd, use fstring, ""
        '        self.cmd(f"afd profile usage -g {resource_group} --profile-name {profile_name}", checks=usage_checks)',
        # one line docstring '''
        '        self.cmd("""afd profile usage -g {resource_group} --profile-name {profile_name}""", checks=usage_checks)',
        # one line docstring """
        '        self.cmd("""afd profile usage -g {resource_group} --profile-name {profile_name}""", checks=usage_checks)',
        # .format
        '        self.cmd("afd profile usage -g {} --profile-name {}".format(group, name)',
        # %s
        '        self.cmd("afd profile usage -g %s --profile-name %s", group, name)',
        # end with hashtag, should match.
        '        self.cmd(f"afd profile usage -g {resource_group} --profile-name {profile_name}", checks=usage_checks) #  xxx',
        # start with hashtag, shouldn't match.
        '        # self.cmd(f"afd profile usage -g {resource_group} --profile-name {profile_name}", checks=usage_checks)',
        # start with blanks, match *_cmd = ''.
        '    stop_cmd = \'aks stop --resource-group={resource_group} --name={name}\'\n',
        # start with blanks, match *_cmd = "".
        '    enable_cmd = "aks enable-addons --addons confcom --resource-group={resource_group} --name={name} -o json"\n',
        # start with blanks, match *_cmd = f''.
        '    disable_cmd = f\'aks disable-addons --addons confcom --resource-group={resource_group} --name={name} -o json\'\n',
        # start with blanks, match *_cmd = f"".
        '    browse_cmd = f"aks browse --resource-group={resource_group} --name={name} --listen-address=127.0.0.1 --listen-port=8080 --disable-browser"\n',
    ]
    ref = get_all_tested_commands_from_regex(lines)
    pprint(ref, width=1000)
    assert len(ref) == 15


# multiple lines test
def test_multiple_lines_regex():
    lines = [
        # start with blanks, self.cmd, one cmd line, multiple checks.
        '        self.cmd(\'aks list -g {resource_group}\', checks=[\n',
        '            self.check(\'[0].type\', \'{resource_type}\'),\n',
        '            StringContainCheck(aks_name),\n',
        '            StringContainCheck(resource_group)\n',
        '        ])\n',
        # start with blanks, self.cmd, multiple cmd lines, multiple checks.
        '        self.cmd(\'image builder create -n {tmpl_02} -g {rg} --identity {ide} --scripts {script} --image-source {img_src} --build-timeout 22\'\n',
        '                 \' --managed-image-destinations img_1=westus \' + out_3,\n',
        '                 checks=[\n',
        '                     self.check(\'name\', \'{tmpl_02}\'), self.check(\'provisioningState\', \'Succeeded\'),\n',
        '                     self.check(\'length(distribute)\', 2),\n',
        '                     self.check(\'distribute[0].imageId\', \'/subscriptions/{sub}/resourceGroups/{rg}/providers/Microsoft.Compute/images/img_1\'),\n',
        '                     self.check(\'distribute[0].location\', \'westus\'),\n',
        '                     self.check(\'distribute[0].runOutputName\', \'img_1\'),\n',
        '                     self.check(\'distribute[0].type\', \'ManagedImage\'),\n',
        '                     self.check(\'distribute[1].imageId\', \'/subscriptions/{sub}/resourceGroups/{rg}/providers/Microsoft.Compute/images/img_2\'),\n',
        '                     self.check(\'distribute[1].location\', \'centralus\'),\n',
        '                     self.check(\'distribute[1].runOutputName\', \'img_2\'),\n',
        '                     self.check(\'distribute[1].type\', \'ManagedImage\'),\n',
        '                     self.check(\'buildTimeoutInMinutes\', 22)\n',
        '                 ])\n',
        # start with blanks, characters, self.cmd, but have line break at self.cmd(
        '    ipprefix_id = self.cmd(\n',
        '        \'az network public-ip prefix create -g {rg} -n {ipprefix_name} --location {location} --length 29\'). \\n',
        '        get_output_in_json().get("id")\n',
        # start with blanks, match *_cmd = '', multiple lines.
        '    create_cmd = \'aks create -g {resource_group} -n {name} -p {dns_name_prefix} --ssh-key-value {ssh_key_value} \' \\n',
        '                 \'-l {location} --service-principal {service_principal} --client-secret {client_secret} -k {k8s_version} \' \\n',
        '                 \'--node-vm-size {vm_size} \' \\n',
        '                 \'--tags scenario_test -c 1 --no-wait\'\n',
        '    update_cmd = \'aks update --resource-group={resource_group} --name={name} \' \\n',
        '                 \'--aad-admin-group-object-ids 00000000-0000-0000-0000-000000000002 \' \\n',
        '                 \'--aad-tenant-id 00000000-0000-0000-0000-000000000003 -o json\'\n',
        '    enable_autoscaler_cmd = \'aks update --resource-group={resource_group} --name={name} \' \\n',
        '                            \'--tags {tags} --enable-cluster-autoscaler --min-count 2 --max-count 5\'\n',
        '    disable_autoscaler_cmd = \'aks update --resource-group={resource_group} --name={name} \' \\n',
        '                             \'--tags {tags} --disable-cluster-autoscaler\'\n',
        '    create_spot_node_pool_cmd = \'aks nodepool add \' \\n',
        '                                \'--resource-group={resource_group} \' \\n',
        '                                \'--cluster-name={name} \' \\n',
        '                                \'-n {spot_node_pool_name} \' \\n',
        '                                \'--priority Spot \' \\n',
        '                                \'--spot-max-price {spot_max_price} \' \\n',
        '                                \'-c 1\'\n',
        '    create_ppg_node_pool_cmd = \'aks nodepool add \' \\n',
        '                               \'--resource-group={resource_group} \' \\n',
        '                               \'--cluster-name={name} \' \\n',
        '                               \'-n {node_pool_name} \' \\n',
        '                               \'--ppg={ppg} \'\n',
        '    upgrade_node_image_only_cluster_cmd = \'aks upgrade \' \\n',
        '                                          \'-g {resource_group} \' \\n',
        '                                          \'-n {name} \' \\n',
        '                                          \'--node-image-only \' \\n',
        '                                          \'--yes\'\n',
        '    upgrade_node_image_only_nodepool_cmd = \'aks nodepool upgrade \' \\n',
        '                                           \'--resource-group={resource_group} \' \\n',
        '                                           \'--cluster-name={name} \' \\n',
        '                                           \'-n {node_pool_name} \' \\n',
        '                                           \'--node-image-only \' \\n',
        '                                           \'--no-wait\'\n',
        '    get_nodepool_cmd = \'aks nodepool show \' \\n',
        '                       \'--resource-group={resource_group} \' \\n',
        '                       \'--cluster-name={name} \' \\n',
        '                       \'-n {node_pool_name} \'\n',
        # start with blanks, match *_cmd = '', multiple lines, use .format
        '    install_cmd = \'aks install-cli --client-version={} --install-location={} --base-src-url={} \' \\n',
        '                  \'--kubelogin-version={} --kubelogin-install-location={} --kubelogin-base-src-url={}\'.format(version,\n',
        '                                                                                                              ctl_temp_file,\n',
        '                                                                                                              "",\n',
        '                                                                                                              version,\n',
        '                                                                                                              login_temp_file,\n',
        '                                                                                                              "")\n',
        # start with blanks, match *_cmd, use docstring """
        '        create_cmd = """storage account create -n {sc} -g {rg} -l eastus2euap --enable-files-adds --domain-name\n',
        '    {domain_name} --net-bios-domain-name {net_bios_domain_name} --forest-name {forest_name} --domain-guid\n',
        '    {domain_guid} --domain-sid {domain_sid} --azure-storage-sid {azure_storage_sid}"""\n',
        '        update_cmd = """storage account update -n {sc} -g {rg} --enable-files-adds --domain-name {domain_name}\n',
        '    --net-bios-domain-name {net_bios_domain_name} --forest-name {forest_name} --domain-guid {domain_guid}\n',
        '    --domain-sid {domain_sid} --azure-storage-sid {azure_storage_sid}"""\n',
        # start with blanks, match *_cmd, use docstring '''
        '        update_cmd = \'\'\'storage account update -n {sc} -g {rg} --enable-files-adds --domain-name {domain_name}\n',
        '    --net-bios-domain-name {net_bios_domain_name} --forest-name {forest_name} --domain-guid {domain_guid}\n',
        '    --domain-sid {domain_sid} --azure-storage-sid {azure_storage_sid}\'\'\'\n',
        # start with blanks, match *_cmd*, .format
        '        create_cmd1 = \'az storage account create -n {} -g {} --routing-choice MicrosoftRouting --publish-microsoft-endpoint true\'.format('
        '        name1, resource_group)',
        # start with blanks, match .cmd
        '    test.cmd(\'az billing account list \'',
        '             \'--expand "soldTo,billingProfiles,billingProfiles/invoiceSections"\',',
        '             checks=[])',
        # start with blanks, match *Command
        '        runCommand = \'aks command invoke -g {resource_group} -n {name} -o json -c "kubectl get pods -A"\'',
        '        self.cmd(runCommand, [',
        '            self.check(\'provisioningState\', \'Succeeded\'),',
        '            self.check(\'exitCode\', 0),',
        '        ])',
        # start with blanks, match *command, use fstring, single quotation marks
        '    command = f\'afd origin-group update -g {resource_group_name} --profile-name {profile_name} \' ',
        '              f\'--origin-group-name {origin_group_name}\'',
        # string splicing (+)
        '    self.cmd(\'spring-cloud app deployment create -g {resourceGroup} -s {serviceName} --app {app} -n green\'\n',
        '             + \' --container-image {containerImage} --registry-username PLACEHOLDER --registry-password PLACEHOLDER\',\n',
        '             checks=[\n',
        '                 self.check(\'name\', \'green\'),\n',
        '             ])\n',
        # --format vs .format
        '    self.cmd(\n',
        '        \'appconfig kv import -n {config_store_name} -s {import_source} --path "{strict_import_file_path}" --format {imported_format} --profile {profile} --strict -y\')',
    ]
    ref = get_all_tested_commands_from_regex(lines)
    pprint(ref, width=1000)
    assert len(ref) == 22


def test_detect_new_command():
    commands = []
    lines = [
        'with self.command_group(\'disk\', compute_disk_sdk, operation_group=\'disks\', min_api=\'2017-03-30\') as g:',
        # 1.`+    g.command(xxx)`
        '+    g.command(\'list-instances\', \'list\', command_type=compute_vmss_vm_sdk)',
        # 2.`+    g.custom_command(xxx)`
        '+    g.custom_command(\'create\', \'create_managed_disk\', supports_no_wait=True, table_transformer=transform_disk_show_table_output, validator=process_disk_or_snapshot_create_namespace)',
        # 3.`+    g.custom_show_command(xxx)`
        '+    g.custom_show_command(\'show\', \'get_vmss\', table_transformer=get_vmss_table_output_transformer(self, False))',
        # 4.`+    g.wait_command(xxx)`
        '+    g.wait_command(\'wait\', getter_name=\'get_vmss\', getter_type=compute_custom)',
    ]
    for row_num, line in enumerate(lines):
        command = search_command(line)
        if command:
            cmd = search_command_group(row_num, lines, command)
            if cmd:
                commands.append(cmd)
    pprint(commands)
    assert commands == ['disk list-instances', 'disk create', 'disk show', 'disk wait']


def test_detect_new_params():
    parameters = []
    lines = [
        # without scope
        '    with self.argument_context(\'disk\') as c:',
        '+        c.argument(\'network_policy\')',
        '+        c.argument(\'zone\', zone_type, min_api=\'2017-03-30\', options_list=[\'--zone\']) ',
        # scope
        '    for scope in [\'disk\', \'snapshot\']:',
        '        with self.argument_context(scope) as c:',
        '+            c.argument(\'size_gb\', options_list=[\'--size-gb\', \'-z\'], help=\'size in GB. Max size: 4095 GB (certain preview disks can be larger).\', type=int)',
        # scope with multi args
        '    for scope in [\'signalr create\', \'signalr update\']:',
        '        with self.argument_context(scope, arg_group=\'Network Rule\') as c:',
        '+            c.argument(\'default_action\', arg_type=get_enum_type([\'Allow\', \'Deny\']), help=\'Default action to apply when no rule matches.\', required=False)',
        # scope AND format
        '    for scope in [\'create\', \'update\']:',
        '        with self.argument_context(\'vmss run-command {}\'.format(scope)) as c:',
        '+            c.argument(\'vmss_name\', run_cmd_vmss_name)',
        # scope AND format
        '    for scope in [\'vm\', \'vmss\']:',
        '        with self.argument_context(\'{} stop\'.format(scope)) as c:',
        '+            c.argument(\'skip_shutdown\', action=\'store_true\', help=\'Skip shutdown and power-off immediately.\', min_api=\'2019-03-01\')',
        # multiple `[]`
        '    with self.argument_context(\'acr connected-registry create\') as c:',
        '+        c.argument(\'client_token_list\', options_list=[\'--client-tokens\'], nargs=\'+\', help=\'Specify the client access to the repositories in the connected registry. It can be in the format [TOKEN_NAME01] [TOKEN_NAME02]...\')',
        '+        c.argument(\'notifications\', options_list=[\'--notifications\'], nargs=\'+\', help=\'List of artifact pattern for which notifications need to be generated. Use the format "--notifications [PATTERN1 PATTERN2 ...]".\')',
        # multiple lines
        '    with self.argument_context(\'webapp update\') as c:',
        '+        c.argument(\'skip_custom_domain_verification\',',
        '+                   help="If true, custom (non *.azurewebsites.net) domains associated with web app are not verified",',
        '+                   arg_type=get_three_state_flag(return_label=True), deprecate_info=c.deprecate(expiration=\'3.0.0\'))',
        # options_list=[""] double quotes
        '    with self.argument_context(\'webapp update\') as c:',
        '+        c.argument(\'minimum_elastic_instance_count\', options_list=["--minimum-elastic-instance-count", "-i"], type=int, is_preview=True, help="Minimum number of instances. App must be in an elastic scale App Service Plan.")',
        '+        c.argument(\'prewarmed_instance_count\', options_list=["--prewarmed-instance-count", "-w"], type=int, is_preview=True, help="Number of preWarmed instances. App must be in an elastic scale App Service Plan.")',
        # self.argument_context with multi args
        '    with self.argument_context(\'appconfig kv import\', arg_group=\'File\') as c:',
        '+        c.argument(\'strict\', validator=validate_strict_import, arg_type=get_three_state_flag(), help="Delete all other key-values in the store with specified prefix and label", is_preview=True)',
        '    with self.argument_context(\'snapshot\', resource_type=ResourceType.MGMT_COMPUTE, operation_group=\'snapshots\') as c:',
        '+        c.argument(\'snapshot_name\', existing_snapshot_name, id_part=\'name\', completer=get_resource_name_completion_list(\'Microsoft.Compute/snapshots\'))',
    ]
    # pattern = r'\+\s+c.argument\((.*)\)?'
    for row_num, line in enumerate(lines):
        params, _ = search_argument(line)
        if params:
            cmds = search_argument_context(row_num, lines)
            # print(cmds)
            for cmd in cmds:
                parameters.append([cmd, params])
                continue
    pprint(parameters)
    assert parameters == [
        ['disk', ['--network-policy']],
        ['disk', ['--zone']],
        ['disk', ['--size-gb,', '-z']],
        ['snapshot', ['--size-gb,', '-z']],
        ['signalr create', ['--default-action']],
        ['signalr update', ['--default-action']],
        ['vmss run-command create', ['--vmss-name']],
        ['vmss run-command update', ['--vmss-name']],
        ['vm stop', ['--skip-shutdown']],
        ['vmss stop', ['--skip-shutdown']],
        ['acr connected-registry create', ['--client-tokens']],
        ['acr connected-registry create', ['--notifications']],
        ['webapp update', ['--skip-custom-domain-verification']],
        ['webapp update', ['--minimum-elastic-instance-count,', '-i']],
        ['webapp update', ['--prewarmed-instance-count,', '-w']],
        ['appconfig kv import', ['--strict']],
        ['snapshot', ['--snapshot-name']],
    ]


if __name__ == '__main__':
    test_one_line_regex()
    test_multiple_lines_regex()
    test_detect_new_command()
    test_detect_new_params()
