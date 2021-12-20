lines = [
    '+             # c.argument(\'architecture\', min_api=\'2021-04-01\', arg_type=get_enum_type(self.get_models(\'Architecture\', operation_group=operation_group)), help=\'Set Architecture on Managed Disk or Snapshot\', is_preview=True)',
    '+             c.argument(\'architecture\', min_api=\'2021-04-01\', arg_type=get_enum_type([\'x64\', \'Arm64\']), help=\'Set Architecture on Managed Disk or Snapshot\', is_preview=True)',
    '+        c.argument(\'no_wait_h\', help="Do not wait for the Agent Pool to complete action and return immediately after queuing the request.", action=\'store_true\')',
    '+        c.argument(\'registry_name\', options_list=[\'--registry\', \'-r\'])',
    '+        g.command(\'delete\', \'acr_connected_registry_delete\')',
    '+        g.show_command(\'show\', \'acr_connected_registry_show\')',
    '+     if architecture is not None:',
    '+         if disk.supported_capabilities is None:',
    '+             supportedCapabilities = cmd.get_models(\'SupportedCapabilities\')(architecture=architecture)',
    '+             disk.supported_capabilities = supportedCapabilities',
    '+         else:',
    '+             disk.supported_capabilities.architecture = architecture',
    '+     @ResourceGroupPreparer(name_prefix=\'cli_test_vm_disk_architecture\')',
    '+     def test_vm_disk_architecture(self, resource_group):',
    '+         self.kwargs.update({',
    '+             \'disk1\': \'disk1\',',
    '+             \'disk2\': \'disk2\',',
    '+             \'snapshot1\': \'snapshot1\',',
    '+             \'snapshot2\': \'snapshot2\',',
    '+         })',
    '+ ',
    '+         self.cmd(\'disk create --architecture x64 --size-gb 5 -n {disk1} -g {rg}\')',
    '+         self.cmd(\'disk show -g {rg} -n {disk1}\', checks=[',
    '+             self.check(\'name\', \'{disk1}\'),',
    '+             self.check(\'supportedCapabilities.Architecture\', \'x64\')',
    '+         ])',
    '+         self.cmd(\'disk update --architecture Arm64 -n {disk1} -g {rg}\')',
    '+         self.cmd(\'disk show -g {rg} -n {disk1}\', checks=[',
    '+             self.check(\'name\', \'{disk1}\'),',
    '+             self.check(\'supportedCapabilities.Architecture\', \'Arm64\')',
    '+         ])',
    '+         self.cmd(\'disk create --size-gb 5 -n {disk2} -g {rg}\')',
    '+         self.cmd(\'disk show -g {rg} -n {disk2}\', checks=[',
    '+             self.check(\'name\', \'{disk2}\'),',
    '+             self.check(\'supportedCapabilities\', None)',
    '+         ])',
    '+         self.cmd(\'disk update --architecture Arm64 -n {disk2} -g {rg}\')',
    '+         self.cmd(\'snapshot show -g {rg} -n {disk2}\', checks=[',
    '+             self.check(\'name\', \'{disk2}\'),',
    '+             self.check(\'supportedCapabilities.Architecture\', \'Arm64\')',
    '+         ])',
    '+ ',
    '+         self.cmd(\'snapshot create --architecture x64 --size-gb 5 -n {snapshot1} -g {rg}\')',
    '+         self.cmd(\'snapshot show -g {rg} -n {snapshot1}\', checks=[',
    '+             self.check(\'name\', \'{snapshot1}\'),',
    '+             self.check(\'supportedCapabilities.Architecture\', \'x64\')',
    '+         ])',
    '+         self.cmd(\'snapshot update --architecture Arm64 -n {snapshot1} -g {rg}\')',
    '+         self.cmd(\'snapshot show -g {rg} -n {snapshot1}\', checks=[',
    '+             self.check(\'name\', \'{snapshot1}\'),',
    '+             self.check(\'supportedCapabilities.Architecture\', \'Arm64\')',
    '+         ])',
    '+         self.cmd(\'snapshot create --size-gb 5 -n {snapshot2} -g {rg}\')',
    '+         self.cmd(\'snapshot show -g {rg} -n {snapshot2}\', checks=[',
    '+             self.check(\'name\', \'{snapshot2}\'),',
    '+             self.check(\'supportedCapabilities\', None)',
    '+         ])',
    '+         self.cmd(\'snapshot update --architecture Arm64 -n {snapshot2} -g {rg}\')',
    '+         self.cmd(\'snapshot show -g {rg} -n {snapshot2}\', checks=[',
    '+             self.check(\'name\', \'{snapshot2}\'),',
    '+             self.check(\'supportedCapabilities.Architecture\', \'Arm64\')',
    '+         ])',
]


def test_regex():
    import re
    import json
    from pprint import pprint
    parameters = []
    commands = []
    all = []
    for line in lines:
        pattern = r'\+\s+c.argument\((.*)\)'
        ref = re.findall(pattern, line)
        if ref:
            print(ref)
            if 'options_list' in ref[0]:
                sub_pattern = r'options_list=(.*)'
                parameter = re.findall(sub_pattern, ref[0])[0].replace('\'', '"')
                parameters.append(json.loads(parameter))
            else:
                parameter = '--' + ref[0].split(',')[0].strip("'").replace('_', '-')
                parameters.append([parameter])
        pattern2 = r'\+\s+g.(?:\w+)?command\((.*)\)'
        ref = re.findall(pattern2, line)
        if ref:
            print(ref)
            command = ref[0].split(',')[0].strip("'")
            commands.append(command)
        pattern3 = r'\+\s+(.*)'
        ref = re.findall(pattern3, line)
        if ref:
            all += ref
    pprint(all)
    pprint(commands)
    pprint(parameters)
    flag = False
    for opt_list in parameters:
        for opt in opt_list:
            for code in all:
                if opt in code:
                    print('True', opt_list, code)
                    flag = True
                    break
            if flag:
                break


if __name__ == '__main__':
    test_regex()