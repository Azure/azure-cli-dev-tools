# -----------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for
# license information.
# -----------------------------------------------------------------------------

import os
import time
import yaml

from knack.help_files import helps
from knack.log import get_logger
from knack.util import CLIError

from azdev.utilities import (
    heading, subheading, display, get_path_table, require_azure_cli, filter_by_git_diff)
from azdev.utilities.path import get_cli_repo_path, get_ext_repo_paths, get_azdev_repo_path, find_files
from .util import filter_modules, merge_exclusion


logger = get_logger(__name__)
CHECKERS_PATH = 'azdev.operations.linter.pylint_checkers'

def run_cmdcov():
    logger.info('enter cmdcov')


# pylint:disable=too-many-locals, too-many-statements, too-many-branches
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

    # selected_mod_names = list(selected_modules['mod'].keys()) + list(selected_modules['core'].keys()) + \
    #                      list(selected_modules['ext'].keys())
    # selected_mod_paths = list(selected_modules['mod'].values()) + list(selected_modules['core'].values()) + \
    #                      list(selected_modules['ext'].values())

    selected_mod_names = list(selected_modules['mod'].keys())
    selected_mod_paths = list(selected_modules['mod'].values())
    # exclude mod
    # exclude_mod = ['acs', 'apim', 'aro', 'batch', 'billing', 'cdn', 'cloud', 'dla', 'extension', 'hdinsight', 'lab',
    #                'marketplaceordering', 'profile', 'rdbms', 'relay', 'servicebus', 'storage']
    # for mod in exclude_mod:
    #     selected_mod_names.remove(mod)
    #     selected_mod_paths.remove('c:\\code\\azure-cli\\src\\azure-cli\\azure\\cli\\command_modules\\{}'.format(mod))
    # Other Errors TODO
    selected_mod_names.remove('appservice')
    selected_mod_paths.remove('c:\\code\\azure-cli\\src\\azure-cli\\azure\\cli\\command_modules\\appservice')
    selected_mod_names.remove('batchai')
    selected_mod_paths.remove('c:\\code\\azure-cli\\src\\azure-cli\\azure\\cli\\command_modules\\batchai')
    # dir not exist TODO
    selected_mod_names.remove('interactive')
    selected_mod_paths.remove('c:\\code\\azure-cli\\src\\azure-cli\\azure\\cli\\command_modules\\interactive')

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

    all_test_commands = _get_all_commands(selected_mod_names, loaded_help)
    all_tested_commands = _get_all_tested_commands(selected_mod_names, selected_mod_paths)
    command_coverage, all_untested_commands = _run_commands_coverage(all_test_commands, all_tested_commands)
    html_file = _render_html(command_coverage, all_untested_commands)

    subheading('Results')
    import webbrowser
    webbrowser.open_new_tab(html_file)


def _get_all_commands(selected_mod_names, loaded_help):
    # selected_mod_names = ['vm']
    exclude_parameters = []
    global_arguments = ['--debug', '--help', '-h', '--only-show-errors', '--output', '-o', '--query', '--query-examples',
                        '--subscription', '--verbose']
    generic_update_parameters = ['--add', '--force-string', '--remove', '--set']
    wait_condition_parameters = ['--created', '--custom', '--deleted', '--exists', '--interval', '--timeout', '--updated']
    other_parameters = [
        '--admin-username', '--admin-password',
        '--capacity-reservation-group', '--capacity-reservation-name',
        '--ids', '--ignore-errors',
        '--location', '-l',
        '--name', '-n', '--no-wait',
        '--username', '-u',
        '--password', '-p',
        '--resource-group', '-g',
        '--tags',
        '--windows-admin-username', '--windows-admin-password',
        '--yes', '-y',
    ]
    exclude_parameters = exclude_parameters + global_arguments + generic_update_parameters + wait_condition_parameters + other_parameters


    all_test_commands = {m: [] for m in selected_mod_names}
    # like module vm have multiple command like vm vmss disk snapshot
    for _, y in loaded_help.items():
        # if x.split()[0] in selected_mod_names:
        if hasattr(y, 'command_source') and y.command_source in selected_mod_names:
            for parameter in y.parameters:
                opt_list = []
                for opt in parameter.name_source:
                    if opt.startswith('-') and opt not in exclude_parameters:
                        opt_list.append(opt)
                if opt_list:
                    all_test_commands[y.command_source].append(f'{y.command} {opt_list}')

    return all_test_commands


def _get_all_tested_commands(selected_mod_names, selected_mod_path):
    import re
    import pprint
    cmd_pattern = r'self.cmd\((?:\'|")(.*)(?:\'|")(.*)?\n'
    # cmd_pattern = r'self.cmd\((?:\'|")(.*)(?:\'|")(?:\).*)?\n'
    quo_pattern = r'(["\'])((?:\\\1|(?:(?!\1)).)*)(\1)'
    end_pattern = r'(\)|checks=|,\n)'
    # selected_mod_names = ['vm']
    all_tested_commands = {m: [] for m in selected_mod_names}
    # selected_mod_path = ['c:\\code\\azure-cli\\src\\azure-cli\\azure\\cli\\command_modules\\vm']
    # selected_mod_path = ['d:\\code\\azure-cli\\src\\azure-cli\\azure\\cli\\command_modules\\vm']
    for idx, path in enumerate(selected_mod_path):
        test_dir = os.path.join(path, 'tests')
        # test_dir = os.path.join(path, 'tests', 'latest')
        files = find_files(test_dir, 'test_*.py')
        # files = filter(lambda f: f.startswith('test_'), os.listdir(test_dir))
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
                            try:
                                command += re.findall(quo_pattern, lines[row_num])[0][1]
                            except Exception as e:
                                # pass
                                print('Exception1', row_num, selected_mod_names[idx], f)
                        else:
                            command = command + ' ' + str(count)
                            all_tested_commands[selected_mod_names[idx]].append(command)
                            row_num += 1
                            count += 1
                    else:
                        row_num += 1
    # pprint.pprint(all_tested_commands[selected_mod_names[idx]], width=500)
    # print(len(all_tested_commands[selected_mod_names[idx]]))
    return all_tested_commands


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


def _run_commands_coverage(all_test_commands, all_tested_commands):
    import ast
    # module: vm
    # percentage: xx.xx%
    # all_untested_commands: {'vm': []}
    command_coverage = {'Total': [0, 0, 0]}
    all_untested_commands = {}
    for module in all_test_commands.keys():
        command_coverage[module] = []
        all_untested_commands[module] = []
    for module in all_test_commands.keys():
        count = 0
        for command in all_test_commands[module]:
            exist_flag = False
            prefix, opt_list = command.rsplit('[', maxsplit=1)[0], ast.literal_eval('[' + command.rsplit('[', maxsplit=1)[1])
            for cmd in all_tested_commands[module]:
                if prefix in cmd:
                    for opt in opt_list:
                        if opt in cmd:
                            count += 1
                            exist_flag = True
                            if exist_flag:
                                break
                if exist_flag:
                    break
            else:
                all_untested_commands[module].append(command)
        try:
            command_coverage[module] = [count, len(all_untested_commands[module]), f'{count / len(all_test_commands[module]):.3%}']
        except:
            print('Exception2', module)
        command_coverage['Total'][0] += count
        command_coverage['Total'][1] += len(all_untested_commands[module])
    command_coverage['Total'][2] = f'{command_coverage["Total"][0] / (command_coverage["Total"][0] + command_coverage["Total"][1]):.3%}'
    print(command_coverage)
    import pprint
    # pprint.pprint(all_untested_commands)
    return command_coverage, all_untested_commands


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


def _render_html(command_coverage, all_untested_commands):
    """
    Return a HTML string
    :param data:
    :param container:
    :param container_url:
    :param testdata:
    :param USER_REPO:
    :param USER_BRANCH:
    :param COMMIT_ID:
    :param USER_LIVE:
    :return:
    """
    logger.warning('Enter render()')
    import time
    date = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())
    html_path = get_html_path(date.split()[0])
    _render_css(html_path)
    content = """
<!DOCTYPE html>
<html>
    <head>
        <meta charset="UTF-8">
        <title>Detail</title>
        <link rel="stylesheet" type="text/css" href="component.css"/>
        <link rel="shortcut icon" href="favicon.ico">
    </head>
<body>
    <div class="container">
        <div class="component">
            <h1>CLI Command Coverage Report</h1>
            <h2>Date: {}</h2>
    """.format(date)

    content += """
                <h2>Tested: {}, Untested: {}, Percentage: {}</h2>
                <p>This is the command coverage report of CLI. Scroll down to see the every module coverage.<br>
                    Any question please contact Azure Cli Team.</p>
    """.format(command_coverage['Total'][0], command_coverage['Total'][1], command_coverage['Total'][2])

    table = """
                <table>
                    <thead>
                    <tr>
                        <th>Module</th>
                        <th>Tested</th>
                        <th>Untested</th>
                        <th>Percentage</th>
                        <th>Percentage</th>
                        <th>Percentage</th>
                        <th>Reports</th>
                    </tr>
                    </thead>
    """

    table += """
                    <tbody>
                    <tr>
                        <td>Total</td>
                        <td>{}</td>
                        <td>{}</td>
                        <td>{}</td>

    """.format(command_coverage['Total'][0], command_coverage['Total'][1], command_coverage['Total'][2])

    if command_coverage['Total'][2] < '30%':
        color = 'red'
    elif command_coverage['Total'][2] < '60%':
        color = 'orange'
    else:
        color = 'green'
    percentage = command_coverage['Total'][2].split('.')[0]
    table += """
                        <td>
                            <div class="single-chart">
                                <svg viewBox="0 0 36 36" class="circular-chart {color}">
                                    <path class="circle-bg"
                                          d="M18 2.0845
          a 15.9155 15.9155 0 0 1 0 31.831
          a 15.9155 15.9155 0 0 1 0 -31.831"
                                    />
                                    <path class="circle"
                                          stroke-dasharray="{percentage}, 100"
                                          d="M18 2.0845
          a 15.9155 15.9155 0 0 1 0 31.831
          a 15.9155 15.9155 0 0 1 0 -31.831"
                                    />
                                    <text x="18" y="20.35" class="percentage">{percentage}%</text>
                                </svg>
                            </div>
                        </td>
                        <td>
                            <div class="progressbar">
                                <div class="{color}" style="width: {percentage}%;">{percentage}%</div>
                            </div>
                        </td>                         
    """.format(color=color, percentage=percentage)

    table += """
                        <td>N/A</td>
                    </tr>
    """

    command_coverage.pop('Total')

    for module, coverage in command_coverage.items():
        # feedback: []
        # find: []
        if coverage:
            reports = '<a href="{module}.html">{module} coverage report</a> '.format(module=module)
            child_html = _render_child_html(module, coverage, all_untested_commands[module])
            with open(f'{html_path}/{module}.html', 'w') as f:
                f.write(child_html)
            try:
                table += """
                  <tr>
                    <td>{}</td>
                    <td>{}</td>
                    <td>{}</td>
                    <td>{}</td>
                """.format(module, coverage[0], coverage[1], coverage[2])
            except:
                print('Exception3', module, coverage, reports)

            try:
                if coverage[2] < '30%':
                    color = 'red'
                elif coverage[2] < '60%':
                    color = 'orange'
                else:
                    color = 'green'
                percentage = coverage[2].split('.')[0]
            except Exception as e:
                print('coverage exception', coverage)
            table += """
                                <td>
                                    <div class="single-chart">
                                        <svg viewBox="0 0 36 36" class="circular-chart {color}">
                                            <path class="circle-bg"
                                                  d="M18 2.0845
                  a 15.9155 15.9155 0 0 1 0 31.831
                  a 15.9155 15.9155 0 0 1 0 -31.831"
                                            />
                                            <path class="circle"
                                                  stroke-dasharray="{percentage}, 100"
                                                  d="M18 2.0845
                  a 15.9155 15.9155 0 0 1 0 31.831
                  a 15.9155 15.9155 0 0 1 0 -31.831"
                                            />
                                            <text x="18" y="20.35" class="percentage">{percentage}%</text>
                                        </svg>
                                    </div>
                                </td>
                                <td>
                                    <div class="progressbar">
                                        <div class="{color}" style="width: {percentage}%;">{percentage}%</div>
                                    </div>
                                </td>                         
            """.format(color=color, percentage=percentage)

            table += """
                                <td>{}</td>
                            </tr>
            """.format(reports)

    table += """
                    </tbody>
                </table>
    """
    content += table

    content += """
                <p class="contact">This is the command coverage report of CLI.<br>
                    Any question please contact Azure Cli Team.</p>
            </div>
        </div><!-- /container -->
    </body>
</html>
    """

    # logger.warning(content)
    # logger.warning('Exit render()')
    with open(f'{html_path}/index.html', 'w') as f:
        f.write(content)

    # copy icon
    import shutil
    import sys
    source = os.path.join(get_azdev_repo_path(), 'azdev', 'operations', 'cmdcov', 'favicon.ico')
    # adding exception handling
    try:
        shutil.copy(source, html_path)
    except IOError as e:
        print("Unable to copy %s" % e)
    except:
        print("Unexpected error:", sys.exc_info())

    return html_path + '/index.html'


def _render_child_html(module, command_coverage, all_untested_commands):
    """
    Return a HTML string
    :param data:
    :param container:
    :param container_url:
    :param testdata:
    :param USER_REPO:
    :param USER_BRANCH:
    :param COMMIT_ID:
    :param USER_LIVE:
    :return:
    """
    # logger.warning('Enter render()')
    import time
    date = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())

    content = """
<!DOCTYPE html>
<html lang="en">
    <head>
        <meta charset="UTF-8">
        <title>Detail</title>
        <link rel="stylesheet" type="text/css" href="component.css"/>
        <link rel="shortcut icon" href="favicon.ico">
    </head>
    <body>
        <div class="container">
            <div class="component">
                <h1>CLI Command Coverage Report</h1>
                <h2>Date: {}</h2>
    """.format(date)

    try:
        content += """
                    <h2>Tested: {}, Untested: {}, Percentage: {}</h2>
                    <p>This is command coverage report of {} module. Scroll down to see the details.<br>
                        Any question please contact Azure Cli Team.<br>
                        <a href="index.html" title="Back to Summary">Back to Homepage</a>.</p>
        """.format(command_coverage[0], command_coverage[1], command_coverage[2], module)
    except:
        print('Exception4', command_coverage, module)

    content += """
                <table>
                    <thead>
                    <tr>
                        <th>Module</th>
                        <th>Untested</th>
                    </tr>
                    </thead>
                    <tbody>    """

    for cmd in all_untested_commands:
        content += """
          <tr>
            <td>{}</td>
            <td>{}</td>
          </tr>
        """.format(module, cmd)

    content += """
                    </tbody>
                </table>
                <p class="contact">This is command coverage report of {} module.<br>
                    Any question please contact Azure Cli Team.<br>
                    <a href="index.html" title="Back to Summary">Back to Homepage</a>.</p>
            </div>
        </div><!-- /container -->
    </body>
</html>
    """.format(module)

    # logger.warning(content)
    # logger.warning('Exit render()')
    return content


def _render_css(html_path):
    content = """
/* Component styles */
.component {
	line-height: 1.5em;
	margin: 0 auto;
	padding: 2em 0 3em;
	width: 100%;
	max-width: 1200px;
	overflow: hidden;
}
.component .contact {
	font-family: "Blokk", Arial, sans-serif;
	color: #d3d3d3;
}
table {
    border: 1px solid black;
    border-collapse: collapse;
    margin-bottom: 3em;
    width: 100%;
    background: #fff;
}
td, th {
    border: 1px solid black;
    padding: 0.75em 1.5em;
    text-align: left;
}
	td.err {
		background-color: #e992b9;
		color: #fff;
		font-size: 0.75em;
		text-align: center;
		line-height: 1;
	}
th {
    background-color: #31bc86;
    font-weight: bold;
    color: #fff;
    white-space: nowrap;
}
tbody th {
	background-color: #2ea879;
}
tbody tr:hover {
    background-color: rgba(129,208,177,.3);
}
td.module, td.command {
	text-transform: capitalize;
}

.single-chart {
  width: 100%;
  justify-content: space-around ;
}

.circular-chart {
  display: block;
  margin: 0px auto;
  max-width: 100%;
  max-height: 50px;
}

.circle-bg {
  fill: none;
  stroke: #eee;
  stroke-width: 3.8;
}

.circle {
  fill: none;
  stroke-width: 2.8;
  stroke-linecap: round;
  animation: progress 1s ease-out forwards;
}

@keyframes progress {
  0% {
    stroke-dasharray: 0 100;
  }
}

.circular-chart.red .circle {
  stroke: red;
}

.circular-chart.orange .circle {
  stroke: #ff9f00;
}

.circular-chart.green .circle {
  stroke: #4CC790;
}

.circular-chart.blue .circle {
  stroke: #3c9ee5;
}

.percentage {
  fill: #666;
  font-family: sans-serif;
  font-size: 0.6em;
  text-anchor: middle;
}


.progressbar {
  background-color: #eee;
  border-radius: 10px;
  /* (height of inner div) / 2 + padding */
  padding: 1px;
}

.progressbar .red {
  background-color: red;
  width: 40%;
  /* Adjust with JavaScript */
  height: 20px;
  border-radius: 10px;
  text-align: center;
  font-size: 0.1em;
}

.progressbar .orange {
  background-color: orange;
  width: 40%;
  /* Adjust with JavaScript */
  height: 20px;
  border-radius: 10px;
  text-align: center;
  font-size: 0.1em;
}

.progressbar .green {
  background-color: green;
  width: 40%;
  /* Adjust with JavaScript */
  height: 20px;
  border-radius: 10px;
  text-align: center;
  font-size: 0.1em;
}
    """
    with open(f'{html_path}/component.css', 'w') as f:
        f.write(content)


def get_html_path(date):
    root_path = get_azdev_repo_path()
    html_path = os.path.join(root_path, 'cmd_coverage', f'{date}')
    if not os.path.exists(html_path):
        os.makedirs(html_path)
    return html_path


def get_container_name():
    """
    Generate container name in storage account. It is also an identifier of the pipeline run.
    :return:
    """
    import datetime
    import random
    import string
    logger.warning('Enter get_container_name()')
    time = datetime.datetime.now().strftime('%Y%m%d-%H%M%S')
    random_id = ''.join(random.choice(string.digits) for _ in range(6))
    name = time + '-' + random_id
    logger.warning('Exit get_container_name()')
    return name


def upload_files(container, html_path, account_key):
    """
    Upload html and json files to container
    :param container:
    :return:
    """
    logger.warning('Enter upload_files()')

    # Create container
    cmd = 'az storage container create -n {} --account-name clitestresultstac --account-key {} --public-access container'.format(container, account_key)
    os.system(cmd)

    # Upload files
    for root, dirs, files in os.walk(html_path):
        for name in files:
            if name.endswith('html') or name.endswith('css'):
                fullpath = os.path.join(root, name)
                cmd = 'az storage blob upload -f {} -c {} -n {} --account-name clitestresultstac'
                cmd = cmd.format(fullpath, container, name)
                logger.warning('Running: ' + cmd)
                os.system(cmd)

    logger.warning('Exit upload_files()')


if __name__ == '__main__':
    pass
    # _get_all_tested_commands(['a'], ['b'])
    # regex2()
    # regex3()
