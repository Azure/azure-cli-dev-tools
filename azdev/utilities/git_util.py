# -----------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for
# license information.
# -----------------------------------------------------------------------------

import os

from knack.log import get_logger
from knack.util import CLIError

logger = get_logger(__name__)


def filter_by_git_diff(selected_modules, git_source, git_target, git_repo):
    if not any([git_source, git_target, git_repo]):
        return selected_modules

    if not all([git_target, git_repo]):
        raise CLIError('usage error: [--src NAME]  --tgt NAME --repo PATH')

    files_changed = diff_branches(git_repo, git_target, git_source)
    mods_changed = summarize_changed_mods(files_changed)

    repo_path = str(os.path.abspath(git_repo)).lower()
    to_remove = {'mod': [], 'core': [], 'ext': []}
    for key in selected_modules:
        for name, path in selected_modules[key].items():
            path = path.lower()
            if path.startswith(repo_path):
                if name in mods_changed:
                    # has changed, so do not filter out
                    continue
            # if not in the repo or has not changed, filter out
            to_remove[key].append(name)

    # remove the unchanged modules
    for key, value in to_remove.items():
        for name in value:
            selected_modules[key].pop(name)
    logger.info('Filtered out: %s', to_remove)

    return selected_modules


def summarize_changed_mods(files_changed):
    from azdev.utilities import extract_module_name

    mod_set = set()
    for f in files_changed:
        try:
            mod_name = extract_module_name(f)
        except CLIError:
            # some files aren't part of a module
            continue
        mod_set.add(mod_name)
    return list(mod_set)


def diff_branches(repo, target, source):
    """ Returns a list of files that have changed in a given repo
        between two branches. """
    try:
        import git  # pylint: disable=unused-import,unused-variable
        import git.exc as git_exc
        import gitdb
    except ImportError as ex:
        raise CLIError(ex)

    from git import Repo
    try:
        git_repo = Repo(repo)
    except (git_exc.NoSuchPathError, git_exc.InvalidGitRepositoryError):
        raise CLIError('invalid git repo: {}'.format(repo))

    def get_commit(branch):
        try:
            return git_repo.commit(branch)
        except gitdb.exc.BadName:
            raise CLIError('usage error, invalid branch: {}'.format(branch))

    if source:
        source_commit = get_commit(source)
    else:
        source_commit = git_repo.head.commit
    target_commit = get_commit(target)

    logger.info('Filtering down to modules which have changed based on:')
    logger.info('cd %s', repo)
    logger.info('git --no-pager diff %s..%s --name-only -- .\n', target_commit, source_commit)

    diff_index = target_commit.diff(source_commit)
    return [diff.b_path for diff in diff_index]


def diff_branches_detail(repo, target, source, exclusions=None):
    """ Returns compare results of files that have changed in a given repo between two branches.
        Only focus on these files: _params.py, commands.py, test_*.py """
    try:
        import git  # pylint: disable=unused-import,unused-variable
        import git.exc as git_exc
        import gitdb
    except ImportError as ex:
        raise CLIError(ex)

    from git import Repo
    try:
        git_repo = Repo(repo)
    except (git_exc.NoSuchPathError, git_exc.InvalidGitRepositoryError):
        raise CLIError('invalid git repo: {}'.format(repo))

    def get_commit(branch):
        try:
            return git_repo.commit(branch)
        except gitdb.exc.BadName:
            raise CLIError('usage error, invalid branch: {}'.format(branch))

    if source:
        source_commit = get_commit(source)
    else:
        source_commit = git_repo.head.commit
    target_commit = get_commit(target)

    logger.info('Filtering down to modules which have changed based on:')
    logger.info('cd %s', repo)
    logger.info('git --no-pager diff %s..%s --name-only -- .\n', target_commit, source_commit)

    diff_index = target_commit.diff(source_commit)
    from difflib import context_diff
    import re
    import json
    parameters = []
    commands = []
    all = []
    lines = []
    flag = False
    exec_state = True
    import yaml
    from azdev.utilities.path import get_cli_repo_path
    for diff in diff_index:
        filename = diff.a_path.split('/')[-1]
        if 'params' in filename or 'commands' in filename or re.findall(r'test_.*.py', filename):
            pattern = r'\+\s+c.argument\((.*)\)'
            lines = list(
                context_diff(diff.a_blob.data_stream.read().decode("utf-8").splitlines(True) if diff.a_blob else [],
                             diff.b_blob.data_stream.read().decode("utf-8").splitlines(True) if diff.b_blob else [],
                             'Original', 'Current'))
        for row_num, line in enumerate(lines):
            if 'params.py' in filename:
                ref = re.findall(pattern, line)
                if ref:
                    param_name = ref[0].split(',')[0].strip("'")
                    if 'options_list' in ref[0]:
                        # TODO
                        sub_pattern = r'options_list=(.*)[,)]'
                        params = json.loads(re.findall(sub_pattern, ref[0])[0].replace('\'', '"'))
                        # parameters.append(json.loads(parameter))
                    else:

                        params = ['--' + param_name.replace('_', '-')]
                        # parameters.append([parameter])
                    offset = -1
                    while row_num > 0:
                        row_num -= 1
                        # '--- 156,163 ----'
                        sub_pattern = r'--- (\d{0,}),(?:\d{0,}) ----'
                        idx = re.findall(sub_pattern, lines[row_num])
                        offset += 1
                        if idx:
                            idx = int(idx[0]) + offset
                            break
                    with open(os.path.join(get_cli_repo_path(), diff.a_path), encoding='utf-8') as f:
                        param_lines = f.readlines()
                    while idx > 0:
                        idx -= 1
                        # with self.argument_context(scope) as c:
                        # with self.argument_context('') as c
                        sub_pattern = r'with self.argument_context\(\'?(.*)\'?\)'
                        cmds = re.findall(sub_pattern, param_lines[idx])
                        if cmds:
                            if cmds[0] != 'scope':
                                cmds = [cmds.strip('')]
                                break
                            else:
                                # for scope in ['disk', 'snapshot']:
                                sub_pattern = r'for scope in (.*):'
                                cmds = json.loads(re.findall(sub_pattern, param_lines[idx - 1])[0].replace('\'', '"'))
                                break
                    exclude_flag = False
                    for k, v in exclusions.items():
                        for cmd in cmds:
                            if cmd in k:
                                if 'parameters' in v:
                                    for m, n in v['parameters'].items():
                                        if param_name in m and 'missing_parameter_coverage' in n['rule_exclusions']:
                                            exclude_flag = True
                                            break
                                elif 'rule_exclusions' in v:
                                    if 'missing_command_coverage' in v['rule_exclusions']:
                                        exclude_flag = True
                                        break
                            if exclude_flag:
                                break
                        if exclude_flag:
                            break
                    if not exclude_flag:
                        parameters.append([cmds, params])
            if 'commands.py' in filename:
                pattern = r'\+\s+g.(?:\w+)?command\((.*)\)'
                ref = re.findall(pattern, line)
                if ref:
                    command = ref[0].split(',')[0].strip("'")
                    offset = -1
                    while row_num > 0:
                        row_num -= 1
                        # '--- 156,163 ----'
                        sub_pattern = r'--- (\d{0,}),(?:\d{0,}) ----'
                        idx = re.findall(sub_pattern, lines[row_num])
                        offset += 1
                        if idx:
                            idx = int(idx[0]) + offset
                            break
                    with open(os.path.join(get_cli_repo_path(), diff.a_path), encoding='utf-8') as f:
                        cmd_lines = f.readlines()
                    while idx > 0:
                        idx -= 1
                        # with self.command_group('local-context',
                        sub_pattern = r'with self.command_group\(\'(.*)\','
                        group = re.findall(sub_pattern, cmd_lines[idx])
                        if group:
                            cmd = group[0] + ' ' + command
                            break
                    for k, v in exclusions.items():
                        if cmd in k and 'rule_exclusions' in v \
                                and 'missing_command_coverage' in v['rule_exclusions']:
                            break
                    else:
                        commands.append(cmd)

            if re.findall(r'test_.*.py', filename):
                pattern = r'\+\s+(.*)'
                NUMBER_SIGN_PATTERN = r'^\+\s*#.*$'
                ref = re.findall(pattern, line)
                if ref and not re.findall(NUMBER_SIGN_PATTERN, line):
                    all += ref
        if re.findall(r'test_.*.yaml', filename) and os.path.exists(os.path.join(get_cli_repo_path(), diff.a_path)):
            with open(os.path.join(get_cli_repo_path(), diff.a_path)) as f:
                records = yaml.load(f, Loader=yaml.Loader) or {}
                for record in records['interactions']:
                    # ['acr agentpool create']
                    command = record['request']['headers'].get('CommandName', [''])[0]
                    # ['-n -r']
                    argument = record['request']['headers'].get('ParameterSetName', [''])[0]
                    if command or argument:
                        all.append(command + ' ' + argument)
    logger.debug('New add parameters: {}'.format(parameters))
    logger.debug('New add commands: {}'.format(commands))
    logger.debug('All added code: {}'.format(all))
    print('New add parameters: {}'.format(parameters))
    print('New add commands: {}'.format(commands))
    print('All added code: {}'.format(all))
    for commands, opt_list in parameters:
        for command in commands:
            for opt in opt_list:
                for code in all:
                    if command in code and opt in code:
                        logger.debug("Find '{}' test case in '{}'".format(command + ' ' + opt, code))
                        flag = True
                        break
                else:
                    logger.error("Can not find '{}' test case".format(command + ' ' + opt))
                    logger.error("Please add some scenario tests for the new parameter")
                    logger.error("Or add the new parameter in linter_exclusions.yml")
                    exec_state = False
                if flag:
                    break
    for command in commands:
        for code in all:
            if command in code:
                logger.debug("Find '{}' test case in '{}'".format(command, code))
                break
        else:
            logger.error("Can not find '{}' test case".format(command))
            logger.error("Please add some scenario tests for the new command")
            logger.error("Or add the new command in linter_exclusions.yml")
            exec_state = False
    return exec_state
