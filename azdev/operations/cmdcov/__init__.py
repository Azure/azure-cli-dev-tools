# -----------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for
# license information.
# -----------------------------------------------------------------------------

import os


# import sys
# import time
# import yaml
#
# from knack.help_files import helps
# from knack.log import get_logger
# from knack.util import CLIError
#
# from azdev.utilities import (
#     heading, subheading, display, get_path_table, require_azure_cli, filter_by_git_diff)
# from azdev.utilities.path import get_cli_repo_path, get_ext_repo_paths
# from azdev.operations.style import run_pylint
#
# from .util import filter_modules, merge_exclusion
#
# logger = get_logger(__name__)
# CHECKERS_PATH = 'azdev.operations.linter.pylint_checkers'

# def run_cmdcov():
#     logger.info('enter cmdcov')


# pylint:disable=too-many-locals, too-many-statements, too-many-branches
# cmdcov:disable_command=
# cmdcov:disable_module=
def run_cmdcov(modules=None, rule_types=None, rules=None, ci_exclusions=None,
               git_source=None, git_target=None, git_repo=None, include_whl_extensions=False,
               min_severity=None, save_global_exclusion=False):
    require_azure_cli()
    #
    from azure.cli.core import get_default_cli  # pylint: disable=import-error
    from azure.cli.core.file_util import (  # pylint: disable=import-error
        get_all_help, create_invoker_and_load_cmds_and_args)

    heading('CLI Command Coverage')

    # allow user to run only on CLI or extensions
    cli_only = modules == ['CLI']
    ext_only = modules == ['EXT']
    if cli_only or ext_only:
        modules = None

    # needed to remove helps from azdev
    azdev_helps = helps.copy()
    exclusions = {}
    selected_modules = get_path_table(include_only=modules, include_whl_extensions=include_whl_extensions)

    if cli_only:
        selected_modules['ext'] = {}
    if ext_only:
        selected_modules['mod'] = {}
        selected_modules['core'] = {}

    # used to upsert global exclusion
    update_global_exclusion = None
    if save_global_exclusion and (cli_only or ext_only):
        if cli_only:
            update_global_exclusion = 'CLI'
            if os.path.exists(os.path.join(get_cli_repo_path(), 'linter_exclusions.yml')):
                os.remove(os.path.join(get_cli_repo_path(), 'linter_exclusions.yml'))
        elif ext_only:
            update_global_exclusion = 'EXT'
            for ext_path in get_ext_repo_paths():
                if os.path.exists(os.path.join(ext_path, 'linter_exclusions.yml')):
                    os.remove(os.path.join(ext_path, 'linter_exclusions.yml'))
    #
    # filter down to only modules that have changed based on git diff
    selected_modules = filter_by_git_diff(selected_modules, git_source, git_target, git_repo)

    if not any(selected_modules.values()):
        logger.warning('No commands selected to check.')

    selected_mod_names = list(selected_modules['mod'].keys()) + list(selected_modules['core'].keys()) + \
                         list(selected_modules['ext'].keys())
    selected_mod_paths = list(selected_modules['mod'].values()) + list(selected_modules['core'].values()) + \
                         list(selected_modules['ext'].values())

    if selected_mod_names:
        display('Modules: {}\n'.format(', '.join(selected_mod_names)))

    # collect all rule exclusions
    for path in selected_mod_paths:
        exclusion_path = os.path.join(path, 'cmdcov_exclusions.yml')
        if os.path.isfile(exclusion_path):
            with open(exclusion_path) as f:
                mod_exclusions = yaml.safe_load(f)
            merge_exclusion(exclusions, mod_exclusions or {})

    global_exclusion_paths = [os.path.join(get_cli_repo_path(), 'cmdcov_exclusions.yml')]
    try:
        global_exclusion_paths.extend([os.path.join(path, 'cmdcov_exclusions.yml')
                                       for path in (get_ext_repo_paths() or [])])
    except CLIError:
        pass
    for path in global_exclusion_paths:
        if os.path.isfile(path):
            with open(path) as f:
                mod_exclusions = yaml.safe_load(f)
            merge_exclusion(exclusions, mod_exclusions or {})

    start = time.time()
    display('Initializing cmdcov with command table and help files...')
    az_cli = get_default_cli()

    # load commands, args, and help
    create_invoker_and_load_cmds_and_args(az_cli)
    loaded_help = get_all_help(az_cli)

    stop = time.time()
    logger.info('Commands and help loaded in %i sec', stop - start)
    command_loader = az_cli.invocation.commands_loader

    # format loaded help
    loaded_help = {data.command: data for data in loaded_help if data.command}

    # load yaml help
    help_file_entries = {}
    for entry_name, help_yaml in helps.items():
        # ignore help entries from azdev itself, unless it also coincides
        # with a CLI or extension command name.
        if entry_name in azdev_helps and entry_name not in command_loader.command_table:
            continue
        help_entry = yaml.safe_load(help_yaml)
        help_file_entries[entry_name] = help_entry

    # trim command table and help to just selected_modules
    command_loader, help_file_entries = filter_modules(
        command_loader, help_file_entries, modules=selected_mod_names, include_whl_extensions=include_whl_extensions)

    if not command_loader.command_table:
        logger.warning('No commands selected to check.')
    display('command_loader: {}\n'.format(command_loader))

    # all_test_commands = _get_all_commands(selected_mod_names, loaded_help)
    all_tested_commands = _get_all_tested_commands(selected_mod_names, selected_mod_paths)
    # _detect_commands(all_test_commands, all_tested_commands)

    # display('help_file_entries: {}\n'.format(help_file_entries))
    # display('loaded_help: {}\n'.format(loaded_help))
    # display('exclusions: {}\n'.format(exclusions))
    # display('rules: {}\n'.format(rules))
    # display('ci_exclusions: {}\n'.format(ci_exclusions))
    # display('min_severity: {}\n'.format(min_severity))
    # display('update_global_exclusion: {}\n'.format(update_global_exclusion))
    # display('rule_types: {}\n'.format(rule_types))
    # Instantiate and run Linter
    # linter_manager = LinterManager(command_loader=command_loader,
    #                                help_file_entries=help_file_entries,
    #                                loaded_help=loaded_help,
    #                                exclusions=exclusions,
    #                                rule_inclusions=rules,
    #                                use_ci_exclusions=ci_exclusions,
    #                                min_severity=min_severity,
    #                                update_global_exclusion=update_global_exclusion)

    subheading('Results')
    # logger.info('Running linter: %i commands, %i help entries',
    #             len(command_loader.command_table), len(help_file_entries))
    # exit_code = linter_manager.run(
    #     run_params=not rule_types or 'params' in rule_types,
    #     run_commands=not rule_types or 'commands' in rule_types,
    #     run_command_groups=not rule_types or 'command_groups' in rule_types,
    #     run_help_files_entries=not rule_types or 'help_entries' in rule_types)
    # display(os.linesep + 'Run custom pylint rules.')
    # exit_code += pylint_rules(selected_modules)
    # sys.exit(exit_code)


# def pylint_rules(selected_modules):
#     # TODO: support severity for pylint rules
#     from importlib import import_module
#     my_env = os.environ.copy()
#     checker_path = import_module('{}'.format(CHECKERS_PATH)).__path__[0]
#     my_env['PYTHONPATH'] = checker_path
#     checkers = [os.path.splitext(f)[0] for f in os.listdir(checker_path) if
#                 os.path.isfile(os.path.join(checker_path, f)) and f != '__init__.py']
#     enable = [s.replace('_', '-') for s in checkers]
#     pylint_result = run_pylint(selected_modules, env=my_env, checkers=checkers, disable_all=True, enable=enable)
#     if pylint_result and not pylint_result.error:
#         display(os.linesep + 'No violations found for custom pylint rules.')
#         display('Linter: PASSED\n')
#     if pylint_result and pylint_result.error:
#         display(pylint_result.error.output.decode('utf-8'))
#         display('Linter: FAILED\n')
#     return pylint_result.exit_code
#
#
# def linter_severity_choices():
#     return [str(severity.name).lower() for severity in LinterSeverity]

def _get_all_commands(selected_mod_names, loaded_help):
    # get all modules
    # selected_mod_names = ['acr']
    selected_mod_names = ['vm']
    # get all submodule TODO
    # {
    #     'vm': [1,2,3],
    #     'network': [1,2,3]
    #  }
    all_test_commands = {m: [] for m in selected_mod_names}
    for x, y in loaded_help.items():
        if x.split()[0] in selected_mod_names:
            if hasattr(y, 'command_source') and y.command_source in selected_mod_names:
                for parameter in y.parameters:
                    for opt in parameter.name_source:
                        if opt.startswith('-'):
                            all_test_commands[y.command_source].append(f'{y.command} {opt}')
    return all_test_commands


def _get_all_tested_commands(selected_mod_names, selected_mod_path):
    import re
    import pprint
    cmd_pattern = r'self.cmd\((?:\'|")(.*)(?:\'|")(.*)?\n'
    # cmd_pattern = r'self.cmd\((?:\'|")(.*)(?:\'|")(?:\).*)?\n'
    quo_pattern = r'(["\'])((?:\\\1|(?:(?!\1)).)*)(\1)'
    end_pattern = r'(\)|checks=|,\n)'
    selected_mod_names = ['vm']
    all_tested_commands = {m: [] for m in selected_mod_names}
    selected_mod_path = ['d:\\code\\azure-cli\\src\\azure-cli\\azure\\cli\\command_modules\\vm']
    for path in selected_mod_path:
        test_dir = os.path.join(path, 'tests', 'latest')
        files = filter(lambda f: f.startswith('test_'), os.listdir(test_dir))
        for f in files:
            # if f != 'test_image_builder_commands.py':
            # if f != 'test_vm_commands.py':
            #     continue
            with open(os.path.join(test_dir, f), 'r') as f:
                lines = f.readlines()
                # test_image_builder_commands.py 44
                total_lines = len(lines)
                row_num = 0
                count = 1
                while row_num < total_lines:
                    if re.findall(cmd_pattern, lines[row_num]):
                        command = re.findall(cmd_pattern, lines[row_num])[0][0]
                        while row_num < total_lines and not re.findall(end_pattern, lines[row_num]):
                            row_num += 1
                            command += re.findall(quo_pattern, lines[row_num])[0][1]
                        else:
                            command = command + ' ' + str(count)
                            all_tested_commands['vm'].append(command)
                            row_num += 1
                            count += 1
                    else:
                        row_num += 1
    pprint.pprint(all_tested_commands['vm'], width=500)
    print(len(all_tested_commands['vm']))


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




def _detect_commands(all_test_commands, all_tested_commands):
    pass


def _generate_html():
    pass

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

if __name__ == '__main__':
    _get_all_tested_commands(['a'], ['b'])
    # regex2()
    # regex3()
