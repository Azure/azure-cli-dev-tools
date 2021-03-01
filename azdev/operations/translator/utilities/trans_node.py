# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
from knack.cli import CLI
import json
from enum import Enum
from collections.abc import KeysView


class AZDevTransNode:
    def to_config(self, ctx):
        raise NotImplementedError()

    @staticmethod
    def process_factory_kwargs(factory_kwargs, convert_cli_ctx=True, convert_enum=True):
        kwargs = {}
        for k, v in factory_kwargs.items():
            if isinstance(v, CLI) and convert_cli_ctx:
                v = '$cli_ctx'
            elif convert_enum and isinstance(v, type) and issubclass(v, Enum):
                v = {
                    '_type': 'Enum',
                    'module': v.__module__,
                    'name': v.__name__,
                    'values': [x.value for x in v],
                }
            elif isinstance(v, KeysView):
                # TODO: Not support this. Needs to handle TYPE_CLIENT_MAPPING to enum in network
                v = list(v)
            kwargs[k] = v
        try:
            json.dumps(kwargs)
        except Exception as ex:
            raise TypeError('factory kwargs cannot dump to json') from ex
        return kwargs
