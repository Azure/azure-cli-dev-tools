# -----------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for
# license information.
# -----------------------------------------------------------------------------

from collections import defaultdict
import os

from azdev.utilities import display, heading, cmd, get_cli_repo_path

SERVICE_TEAM_COLOR = 'e99695'

def list_issues():
    import requests
    import time

    base_url = 'https://api.github.com/repos/Azure/azure-cli/issues?page={}'
    issues = []
    page = 1
    while True:
        url = base_url.format(page)
        display('GET: {}'.format(url))
        response = requests.get(url=url, params={})
        new_issues = response.json()
        display(len(new_issues))
        if new_issues:
            try:
                issues = issues + new_issues
                page += 1
            except TypeError:
                # API rate limit
                time.sleep(10)
        else:
            break
    return issues

def show_diff(old, new):

    from git import Repo

    cli_repo = Repo(get_cli_repo_path())
    old_commit = cli_repo.commit('upstream/{}'.format(old))
    new_commit = cli_repo.commit('upstream/{}'.format(new))
    diff_index = new_commit.diff(old_commit)
    for diff_item in diff_index.iter_change_type('M'):
        item_a = diff_item.a_blob.data_stream.read().decode('utf-8')
        item_b = diff_item.b_blob.data_stream.read().decode('utf-8')
        print('A: ' + item_a)
        print('B: ' + item_b)
