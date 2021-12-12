# -----------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for
# license information.
# -----------------------------------------------------------------------------

import re
from .constant import (CMD_PATTERN, QUO_PATTERN, END_PATTERN, DOCS_END_PATTERN, NOT_END_PATTERN)


def regex(line):
    cmd_pattern = r'self.cmd\(\'(.*)\'\n'
    quo_pattern = r'(["\'])((?:\\\1|(?:(?!\1)).)*)(\1)'
    end_pattern = r'(\)|checks=|,\n)'
    command = ''
    if re.findall(cmd_pattern, line):
        command += re.findall(cmd_pattern, line)
        while not re.findall(end_pattern, line):
            command += re.findall(quo_pattern, line)
            line += 1


def regex2():
    lines = [
        '        self.cmd(\'image builder create -n {tmpl_02} -g {rg} --identity {ide} --scripts {script} --image-source {img_src} --build-timeout 22\'\n',
        '                 \' --managed-image-destinations img_1=westus \' + out_3,\n',
        '                 checks=[\n',
        '                     self.check(\'name\', \'{tmpl_02}\'), self.check(\'provisioningState\', \'Succeeded\'),\n',
        '                     self.check(\'length(distribute)\', 2),\n',
        '                     self.check(\'distribute[0].imageId\', \'/subscriptions/{sub}/resourceGroups/{rg}/providers/Microsoft.Compute/images/img_1\'),\n',
        '                     self.check(\'distribute[0].location\', \'westus\'),\n'
        '                     self.check(\'distribute[0].runOutputName\', \'img_1\'),\n'
        '                     self.check(\'distribute[0].type\', \'ManagedImage\'),\n'
        '                     self.check(\'distribute[1].imageId\', \'/subscriptions/{sub}/resourceGroups/{rg}/providers/Microsoft.Compute/images/img_2\'),\n'
        '                     self.check(\'distribute[1].location\', \'centralus\'),\n'
        '                     self.check(\'distribute[1].runOutputName\', \'img_2\'),\n'
        '                     self.check(\'distribute[1].type\', \'ManagedImage\'),\n'
        '                     self.check(\'buildTimeoutInMinutes\', 22)\n'
        '                 ])\n'
        ]
    # lines[0] = '        self.cmd(\'image builder create -n {tmpl_02} -g {rg} --identity {ide} --scripts {script} --image-source {img_src} --build-timeout 22\'\n'
    # pattern = r'.*self.cmd(.*)\n\''
    # print(re.findall(pattern, lines[0]))
    # lines0 = 'self.cmd(\'image builder create -n {tmpl_02} -g {rg} --identity {ide} --scripts {script} --image-source {img_src} --build-timeout 22\'\n'
    lines0 = '        self.cmd(\'image builder create -n {tmpl_02} -g {rg} --identity {ide} --scripts {script} --image-source {img_src} --build-timeout 22\'\n'

    # pattern = r'self.cmd\(\'(.*)\'\n'
    # ['image builder create -n {tmpl_02} -g {rg} --identity {ide} --scripts {script} --image-source {img_src} --build-timeout 22']
    # res = re.findall(pattern, lines0)

    pattern = r'self.cmd\(\'(.*)\'(\))?\n'
    # [('image builder create -n {tmpl_02} -g {rg} --identity {ide} --scripts {script} --image-source {img_src} --build-timeout 22','')]
    res = re.findall(pattern, lines0)

    print(res)
    print('image builder creat' in res and '-n' in res[0][0])

    lines1 = 'self.cmd(\'image builder create -n {tmpl_02} -g {rg} --identity {ide} --scripts {script} --image-source {img_src} --build-timeout 22\')\n'

    # pattern = r'self.cmd\(\'(.*)\'\)\n'
    # ['image builder create -n {tmpl_02} -g {rg} --identity {ide} --scripts {script} --image-source {img_src} --build-timeout 22']
    # res = re.findall(pattern, lines1)
    pattern = r'self.cmd\(\'(.*)\'\n'
    res = re.findall(pattern, lines0)

    print(res)

    # pattern = r'self.cmd\(\'(.*)\'(\))?\n'  # self.cmd pattern
    # # [('image builder create -n {tmpl_02} -g {rg} --identity {ide} --scripts {script} --image-source {img_src} --build-timeout 22',')')]
    # res = re.findall(pattern, lines1)
    #
    # print(res)
    # print('image builder creat' in res and '-n' in res[0][0])
    #
    # lines2 = '                 \' --managed-image-destinations img_1=westus \' + out_3,\n'
    # # pattern = r'\'.*\'.*\n'
    # # pattern = r"'[^']+'"
    # # pattern = r"([\"'])(?:\\\1|[^\1]+)*\1"
    # pattern = r'(["\'])((?:\\\1|(?:(?!\1)).)*)(\1)'  # 引号 pattern
    # res = re.findall(pattern, lines2)
    #
    # lines3 = 'xxx,checks='
    # lines4 = 'self.cmd(\'image builder create -n {tmpl_02} -g {rg} --identity {ide} --scripts {script} --image-source {img_src} --build-timeout 22\')\n'
    # # check= )
    # lines5 = '                 \' --managed-image-destinations img_1=westus \' + out_3,\n'
    # lines6 = '--attach-data-disks {data_disk} --data-disk-delete-option Detach --data-disk-sizes-gb 3 '
    # lines7 = '    \'--os-disk-size-gb 100 --os-type linux --nsg-rule NONE\',\n'
    # pattern = r'(\)|checks=|,\n)'  # end pattern
    # res = re.findall(pattern, lines3)
    # print(res)
    # res = re.findall(pattern, lines4)
    # print(res)
    # res = re.findall(pattern, lines5)
    # print(res)
    # res = re.findall(pattern, lines6)
    # print(res)
    # res = re.findall(pattern, lines7)
    # print(res)


def regex3():
    line = '            self.cmd("role assignment create --assignee {assignee} --role {role} --scope {scope}")\n'
    # cmd_pattern = r'self.cmd\((\'|")(.*)(\'|")\n'
    # cmd_pattern = r'self.cmd\((\'|")(.*)(\'|")\)?\n'
    # cmd_pattern = r'self.cmd\(\'(.*)\'\).*'
    # cmd_pattern = r'self.cmd\((?:\'|")(.*)(?:\'|")(?:\).*)?\n'
    cmd_pattern = r'self.cmd\((?:\'|")(.*)(?:\'|")(.*)?\n'
    print(re.findall(cmd_pattern, line))
    line = '            self.cmd("role assignment create --assignee {assignee} --role {role} --scope {scope}"\n'
    print(re.findall(cmd_pattern, line))
    line = '            self.cmd(\'role assignment create --assignee {assignee} --role {role} --scope {scope}\')\n'
    print(re.findall(cmd_pattern, line))
    line = '            self.cmd(\'role assignment create --assignee {assignee} --role {role} --scope {scope}\'\n'
    print(re.findall(cmd_pattern, line))
    line = 'abcdefg'
    print(re.findall(cmd_pattern, line))
    line = '     identity_id = self.cmd(\'identity create -g {rg} -n {ide}\').get_output_in_json()[\'clientId\']\n'
    print(re.findall(cmd_pattern, line))
    quo_pattern = r'(["\'])((?:\\\1|(?:(?!\1)).)*)(\1)'
    line = '                 \' --managed-image-destinations img_1=westus \' + out_3,\n'
    print(re.findall(quo_pattern, line))
    line = '                 " --managed-image-destinations img_1=westus " + out_3,\n'
    print(re.findall(quo_pattern, line))


def test_regex4():
    lines = [
'        self.cmd(\'image builder create -n {tmpl_02} -g {rg} --identity {ide} --scripts {script} --image-source {img_src} --build-timeout 22\'\n',
'                 \' --managed-image-destinations img_1=westus \' + out_3,\n',
'                 checks=[\n',
'                     self.check(\'name\', \'{tmpl_02}\'), self.check(\'provisioningState\', \'Succeeded\'),\n',
'                     self.check(\'length(distribute)\', 2),\n',
'                     self.check(\'distribute[0].imageId\', \'/subscriptions/{sub}/resourceGroups/{rg}/providers/Microsoft.Compute/images/img_1\'),\n',
'                     self.check(\'distribute[0].location\', \'westus\'),\n'
'                     self.check(\'distribute[0].runOutputName\', \'img_1\'),\n'
'                     self.check(\'distribute[0].type\', \'ManagedImage\'),\n'
'                     self.check(\'distribute[1].imageId\', \'/subscriptions/{sub}/resourceGroups/{rg}/providers/Microsoft.Compute/images/img_2\'),\n'
'                     self.check(\'distribute[1].location\', \'centralus\'),\n'
'                     self.check(\'distribute[1].runOutputName\', \'img_2\'),\n'
'                     self.check(\'distribute[1].type\', \'ManagedImage\'),\n'
'                     self.check(\'buildTimeoutInMinutes\', 22)\n'
'                 ])\n'
'        self.cmd(\'aks list -g {resource_group}\', checks=[\n',
'            self.check(\'[0].type\', \'{resource_type}\'),\n',
'            StringContainCheck(aks_name),\n',
'            StringContainCheck(resource_group)\n',
'        ])\n',
'    ipprefix_id = self.cmd(\n',
'        \'az network public-ip prefix create -g {rg} -n {ipprefix_name} --location {location} --length 29\'). \\n',
'        get_output_in_json().get("id")\n',
'    create_cmd = \'aks create -g {resource_group} -n {name} -p {dns_name_prefix} --ssh-key-value {ssh_key_value} \' \\n',
'                 \'-l {location} --service-principal {service_principal} --client-secret {client_secret} -k {k8s_version} \' \\n',
'                 \'--node-vm-size {vm_size} \' \\n',
'                 \'--tags scenario_test -c 1 --no-wait\'\n',
'    update_cmd = \'aks update --resource-group={resource_group} --name={name} \' \\n',
'                 \'--aad-admin-group-object-ids 00000000-0000-0000-0000-000000000002 \' \\n',
'                 \'--aad-tenant-id 00000000-0000-0000-0000-000000000003 -o json\'\n',
'    stop_cmd = \'aks stop --resource-group={resource_group} --name={name}\'\n',
'    enable_cmd = \'aks enable-addons --addons confcom --resource-group={resource_group} --name={name} -o json\'\n',
'    enable_autoscaler_cmd = \'aks update --resource-group={resource_group} --name={name} \' \\n',
'                            \'--tags {tags} --enable-cluster-autoscaler --min-count 2 --max-count 5\'\n',
'    disable_cmd = \'aks disable-addons --addons confcom --resource-group={resource_group} --name={name} -o json\'\n',
'    disable_autoscaler_cmd = \'aks update --resource-group={resource_group} --name={name} \' \\n',
'                             \'--tags {tags} --disable-cluster-autoscaler\'\n',
'    browse_cmd = \'aks browse --resource-group={resource_group} --name={name} --listen-address=127.0.0.1 --listen-port=8080 --disable-browser\'\n',
'    install_cmd = \'aks install-cli --client-version={} --install-location={} --base-src-url={} \' \\n',
'                  \'--kubelogin-version={} --kubelogin-install-location={} --kubelogin-base-src-url={}\'.format(version,\n',
'                                                                                                              ctl_temp_file,\n',
'                                                                                                              "",\n',
'                                                                                                              version,\n',
'                                                                                                              login_temp_file,\n',
'                                                                                                              "")\n',
'    create_spot_node_pool_cmd = \'aks nodepool add \' \\n',
'                                \'--resource-group={resource_group} \' \\n',
'                                \'--cluster-name={name} \' \\n',
'                                \'-n {spot_node_pool_name} \' \\n',
'                                \'--priority Spot \' \\n',
'                                \'--spot-max-price {spot_max_price} \' \\n',
'                                \'-c 1\'\n',
'    check_role_assignment_cmd = \'role assignment list --scope={vnet_subnet_id}\'\n',
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
'    uptime_sla_cmd = \'aks update --resource-group={resource_group} --name={name} --uptime-sla --no-wait\'\n',
'    get_nodepool_cmd = \'aks nodepool show \' \\n',
'                       \'--resource-group={resource_group} \' \\n',
'                       \'--cluster-name={name} \' \\n',
'                       \'-n {node_pool_name} \'\n',
'    no_uptime_sla_cmd = \'aks update --resource-group={resource_group} --name={name} --no-uptime-sla\'\n',
'        create_cmd = """storage account create -n {sc} -g {rg} -l eastus2euap --enable-files-adds --domain-name\n',
'    {domain_name} --net-bios-domain-name {net_bios_domain_name} --forest-name {forest_name} --domain-guid\n',
'    {domain_guid} --domain-sid {domain_sid} --azure-storage-sid {azure_storage_sid}"""\n',
'        update_cmd = """storage account update -n {sc} -g {rg} --enable-files-adds --domain-name {domain_name}\n',
'    --net-bios-domain-name {net_bios_domain_name} --forest-name {forest_name} --domain-guid {domain_guid}\n',
'    --domain-sid {domain_sid} --azure-storage-sid {azure_storage_sid}"""\n',
'        update_cmd = \'\'\'storage account update -n {sc} -g {rg} --enable-files-adds --domain-name {domain_name}\n',
'    --net-bios-domain-name {net_bios_domain_name} --forest-name {forest_name} --domain-guid {domain_guid}\n',
'    --domain-sid {domain_sid} --azure-storage-sid {azure_storage_sid}\'\'\'\n',
'        create_cmd1 = \'az storage account create -n {} -g {} --routing-choice MicrosoftRouting --publish-microsoft-endpoint true\'.format('
'        name1, resource_group)',
'    test.cmd(\'az billing account list \'',
'             \'--expand "soldTo,billingProfiles,billingProfiles/invoiceSections"\',',
'             checks=[])',
'        runCommand = \'aks command invoke -g {resource_group} -n {name} -o json -c "kubectl get pods -A"\'',
'        self.cmd(runCommand, [',
'            self.check(\'provisioningState\', \'Succeeded\'),',
'            self.check(\'exitCode\', 0),',
'        ])',
'    command = f\'afd origin-group update -g {resource_group_name} --profile-name {profile_name} \' ',
'              f\'--origin-group-name {origin_group_name}\'',
'        self.cmd(f"afd profile usage -g {resource_group} --profile-name {profile_name}", checks=usage_checks)',
    ]
    total_lines = len(lines)
    row_num = 0
    count = 1
    all_tested_commands = []
    while row_num < total_lines:
        cmd_idx = None
        if re.findall(CMD_PATTERN[0], lines[row_num]):
            cmd_idx = 0
        if cmd_idx is None and re.findall(CMD_PATTERN[1], lines[row_num]):
            cmd_idx = 1
        if cmd_idx is None and re.findall(CMD_PATTERN[2], lines[row_num]):
            cmd_idx = 2
        if cmd_idx is None and re.findall(CMD_PATTERN[3], lines[row_num]):
            cmd_idx = 3
        if cmd_idx is not None:
            command = re.findall(CMD_PATTERN[cmd_idx], lines[row_num])[0]
            while row_num < total_lines:
                if (cmd_idx in [0, 1] and not re.findall(END_PATTERN, lines[row_num])) or \
                   (cmd_idx == 2 and (row_num + 1) < total_lines and re.findall(NOT_END_PATTERN, lines[row_num + 1])):
                    row_num += 1
                    try:
                        command += re.findall(QUO_PATTERN, lines[row_num])[0][1]
                    except Exception as e:
                        # pass
                        print('Exception1', row_num)
                elif cmd_idx == 3 and (row_num + 1) < total_lines and not re.findall(DOCS_END_PATTERN, lines[row_num]):
                    row_num += 1
                    try:
                        command += lines[row_num][:-1]
                    except Exception as e:
                        # pass
                        print('Exception1', row_num)
                else:
                    command = command + ' ' + str(count)
                    all_tested_commands.append(command)
                    row_num += 1
                    count += 1
                    break
            else:
                command = command + ' ' + str(count)
                all_tested_commands.append(command)
                row_num += 1
                count += 1
        else:
            row_num += 1
    from pprint import pprint
    pprint(all_tested_commands, width=1000)
    assert len(all_tested_commands) == 28


if __name__ == '__main__':
    test_regex4()