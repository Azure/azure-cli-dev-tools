# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
from .deprecate_info import build_deprecate_info
from .validator import build_validator
from .trans_node import AZDevTransNode


class ConfigurationCtx:

    def __init__(self, module, imports=None):
        self._arg_type_reference_format_queue = []
        self._output_arg_types = set()
        self._module_name = module.__name__
        self.imports = imports or {}
        self._reversed_imports = dict([(v, k) for k, v in self.imports.items()])
        assert len(self.imports) == len(self._reversed_imports)

    def set_art_type_reference_format(self, to_reference_format):
        assert isinstance(to_reference_format, bool)
        self._arg_type_reference_format_queue.append(to_reference_format)

    @property
    def art_type_reference_format(self):
        if len(self._arg_type_reference_format_queue) > 0:
            return self._arg_type_reference_format_queue[-1]
        else:
            raise ValueError('arg_type_reference_format_queue is empty')

    def unset_art_type_reference_format(self):
        if len(self._arg_type_reference_format_queue) > 0:
            self._arg_type_reference_format_queue.pop()

    def get_import_path(self, module_name, name):
        path = "{}#{}".format(module_name, name)
        return self.simplify_import_path(path)

    def add_output_arg_type(self, register_name):
        assert register_name not in self._output_arg_types
        self._output_arg_types.add(register_name)

    def is_output_arg_type(self, register_name):
        return register_name in self._output_arg_types

    def simplify_import_path(self, path):
        if path in self._reversed_imports:
            path = '${}'.format(self._reversed_imports[path])
        elif path.startswith(self._module_name):
            path = path.replace(self._module_name, '')
        return path

    def get_enum_import_path(self, module_name, name):
        # TODO: Checkout module_name
        path = name
        return path
