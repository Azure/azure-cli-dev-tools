def regex(line):
    import re
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
    import re
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
    import re
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
