# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
import copy
import argparse
from os.path import expanduser
from mock import patch

# Directive not in latest release of sphinx, need to pip install sphinx==1.6.7
from docutils import nodes
from docutils.statemachine import ViewList
from docutils.parsers.rst import directives

from sphinx import addnodes
from sphinx.directives import ObjectDescription
from sphinx.util.compat import Directive
from sphinx.util.nodes import nested_parse_with_titles
from sphinx.util.docfields import Field

from azure.cli.core import MainCommandsLoader, AzCli  # pylint: disable=import-error
from azure.cli.core.commands import AzCliCommandInvoker  # pylint: disable=import-error
from azure.cli.core.parser import AzCliCommandParser  # pylint: disable=import-error
from azure.cli.core._help import AzCliHelp, CliCommandHelpFile, ArgumentGroupRegistry  # pylint: disable=import-error

_USER_HOME = expanduser('~')

_CLI_FIELD_TYPES = [
    Field('summary', label='Summary', has_arg=False,
          names=('summary', 'shortdesc')),
    Field('description', label='Description', has_arg=False,
          names=('description', 'desc', 'longdesc'))
]


class CliBaseDirective(ObjectDescription):
    def handle_signature(self, sig, signode):
        signode += addnodes.desc_addname(sig, sig)
        return sig

    def needs_arglist(self):  # pylint: disable=no-self-use
        return False

    def add_target_and_index(self, name, sig, signode):
        signode['ids'].append(name)

    def get_index_text(self, modname, name):  # pylint: disable=unused-argument, no-self-use
        return name


class CliGroupDirective(CliBaseDirective):
    doc_field_types = copy.copy(_CLI_FIELD_TYPES)
    doc_field_types.extend([
        Field('docsource', label='Doc Source', has_arg=False,
              names=('docsource', 'documentsource')),
        Field('deprecated', label='Deprecated', has_arg=False,
              names=('deprecated'))
    ])


class CliCommandDirective(CliBaseDirective):
    doc_field_types = copy.copy(_CLI_FIELD_TYPES)
    doc_field_types.extend([
        Field('docsource', label='Doc Source', has_arg=False,
              names=('docsource', 'documentsource')),
        Field('deprecated', label='Deprecated', has_arg=False,
              names=('deprecated'))
    ])


class CliArgumentDirective(CliBaseDirective):
    doc_field_types = copy.copy(_CLI_FIELD_TYPES)
    doc_field_types.extend([
        Field('required', label='Required', has_arg=False,
              names=('required')),
        Field('values', label='Allowed values', has_arg=False,
              names=('values', 'choices', 'options')),
        Field('default', label='Default value', has_arg=False,
              names=('default')),
        Field('source', label='Values from', has_arg=False,
              names=('source', 'sources')),
        Field('deprecated', label='Deprecated', has_arg=False,
              names=('deprecated'))
    ])


class CliExampleDirective(CliBaseDirective):
    pass


class AbstractHelpGenDirective(Directive):
    """ Generic Sphinx Directive for generating azure cli documentation.
        Should be overridden for core CLI or CLI extensions documentation
    """

    _INDENT = ' ' * 3
    _DOUBLE_INDENT = _INDENT * 2

    def make_rst(self):  # pylint: disable=too-many-statements, too-many-nested-blocks

        az_cli = AzCli(cli_name='az',
                       commands_loader_cls=MainCommandsLoader,
                       invocation_cls=AzCliCommandInvoker,
                       parser_cls=AzCliCommandParser,
                       help_cls=AzCliHelp)

        with patch('getpass.getuser', return_value='your_system_user_login_name'):
            help_files = self._get_help_files(az_cli)

        doc_source_map = self._load_doc_source_map()
        group_registry = None

        for help_file in help_files:  # pylint: disable=too-many-nested-blocks
            is_command = isinstance(help_file, CliCommandHelpFile)

            # it is top level group az if command is empty
            yield '.. cli{}:: {}'.format('command' if is_command else 'group',
                                         help_file.command if help_file.command else 'az')
            yield ''
            yield '{}:summary: {}'.format(self._INDENT, help_file.short_summary)
            yield '{}:description: {}'.format(self._INDENT, help_file.long_summary)
            if help_file.deprecate_info:
                yield '{}:deprecated: {}'.format(self._INDENT,
                                                 help_file.deprecate_info._get_message(help_file.deprecate_info))  # pylint: disable=protected-access
            doc_source_content = self._get_doc_source_content(doc_source_map, help_file)
            if doc_source_content:
                yield doc_source_content
            yield ''

            if is_command and help_file.parameters:
                group_registry = ArgumentGroupRegistry(
                    [p.group_name for p in help_file.parameters if p.group_name])

                parameter_cmp = lambda p: group_registry.get_group_priority(p.group_name) + str(not p.required) + p.name
                for arg in sorted(help_file.parameters, key=parameter_cmp):
                    yield '{}.. cliarg:: {}'.format(self._INDENT, arg.name)
                    yield ''
                    yield '{}:required: {}'.format(self._DOUBLE_INDENT, arg.required)
                    if arg.deprecate_info:
                        yield '{}:deprecated: {}'.format(self._DOUBLE_INDENT,
                                                         arg.deprecate_info._get_message(arg.deprecate_info))  # pylint: disable=protected-access
                    short_summary = arg.short_summary or ''
                    possible_values_index = short_summary.find(' Possible values include')
                    short_summary_end_idx = possible_values_index if possible_values_index >= 0 else len(short_summary)
                    short_summary = short_summary[0:short_summary_end_idx]
                    short_summary = short_summary.strip()
                    yield '{}:summary: {}'.format(self._DOUBLE_INDENT, short_summary)
                    yield '{}:description: {}'.format(self._DOUBLE_INDENT, arg.long_summary)
                    if arg.choices:
                        yield '{}:values: {}'.format(self._DOUBLE_INDENT,
                                                     ', '.join(sorted([str(x) for x in arg.choices])))
                    if arg.default and arg.default != argparse.SUPPRESS:
                        try:
                            if arg.default.startswith(_USER_HOME):
                                arg.default = arg.default.replace(_USER_HOME, '~').replace('\\', '/')
                        except Exception:  # pylint: disable=broad-except
                            pass
                        try:
                            arg.default = arg.default.replace("\\", "\\\\")
                        except Exception:  # pylint: disable=broad-except
                            pass
                        yield '{}:default: {}'.format(self._DOUBLE_INDENT, arg.default)
                    if arg.value_sources:
                        yield '{}:source: {}'.format(self._DOUBLE_INDENT, ', '.join(self._get_param_value_sources(arg)))
                    yield ''
            yield ''
            if help_file.examples:
                for e in help_file.examples:
                    yield '{}.. cliexample:: {}'.format(self._INDENT, e.short_summary)
                    yield ''
                    yield self._DOUBLE_INDENT + e.command.replace("\\", "\\\\")
                    yield ''

    def run(self):
        node = nodes.section()
        node.document = self.state.document
        result = ViewList()
        for line in self.make_rst():
            result.append(line, '<azhelpgen>')

        nested_parse_with_titles(self.state, result, node)
        return node.children

    def _get_help_files(self, az_cli):
        raise NotImplementedError()

    def _load_doc_source_map(self):
        raise NotImplementedError()

    def _get_doc_source_content(self, doc_source_map, help_file):
        raise NotImplementedError()

    @staticmethod
    def _get_param_value_sources(param):
        commands = []
        for value_source in param.value_sources:
            try:
                commands.append(value_source["link"]["command"])
            except KeyError:
                continue
        return commands


def setup_common_directives(app):
    """ Add common directives to the sphinx app. This should be called by setup(app) which sphinx searches for when
        generating documentation from sphinx extensions.

    :param app: The sphinx app
    :return:
    """

    _add_directive(app, 'cligroup', CliGroupDirective)
    _add_directive(app, 'clicommand', CliCommandDirective)
    _add_directive(app, 'cliarg', CliArgumentDirective)
    _add_directive(app, 'cliexample', CliExampleDirective)


def _add_directive(app, name, cls):
    # check based on similar check in Sphinx().add_directive
    if name not in directives._directives:  # pylint: disable=protected-access
        app.add_directive(name, cls)
