# -----------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for
# license information.
# -----------------------------------------------------------------------------

import json

from knack.log import get_logger
from knack.prompting import prompt_y_n
from knack.util import CLIError

from azdev.utilities import (
    cmd as run_cmd, heading, subheading, display)

logger = get_logger(__name__)


class Data(object):
    def __init__(self, **kw):
        self.__dict__.update(kw)
        if 'properties' in self.__dict__:
            self.__dict__.update(self.properties)
            del self.properties


def delete_groups(cmd, prefixes=None, older_than=6, product='azurecli', cause='automation', yes=False):
    from datetime import datetime, timedelta

    groups = json.loads(run_cmd('az group list -ojson').result)
    groups_to_delete = []

    def _filter_by_tags():
        for group in groups:
            group = Data(**group)

            if not group.tags:
                continue

            tags = Data(**group.tags)
            try:
                date_tag = datetime.strptime(tags.date, '%Y-%m-%dT%H:%M:%SZ')
                curr_time = datetime.utcnow()
                if tags.product == product and tags.cause == cause and (curr_time - date_tag <= timedelta(hours=older_than + 1)):
                    groups_to_delete.append(group.name)
            except AttributeError:
                continue

    def _filter_by_prefix():
        for group in groups:
            group = Data(**group)

            for prefix in prefixes:
                if group.name.startswith(prefix):
                    groups_to_delete.append(group.name)

    def _delete():
        for group in groups_to_delete:
            run_cmd('az group delete -g {} -y --no-wait'.format(group), message=True)

    if prefixes:
        logger.info('Filter by prefix')
        _filter_by_prefix()
    else:
        logger.info('Filter by tags')
        _filter_by_tags

    if not groups_to_delete:
        raise CLIError('No groups meet the criteria to delete.')

    if yes:
        _delete()
    else:
        subheading('Groups to Delete')
        for group in groups_to_delete:
            display('\t{}'.format(group))

        if prompt_y_n('Delete {} resource groups?'.format(len(groups_to_delete)), 'y'):
            _delete()
        else:
            raise CLIError('Command cancelled.')