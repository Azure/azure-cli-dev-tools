from .utilities import AZDevTransDeprecateInfo
from knack.help import _load_help_file


class AZDevTransCommandGroupHelp:

    def __init__(self, help_data):
        assert help_data['type'].lower() == 'group'
        self.short_summary = help_data.get('short-summary', None)
        self.long_summary = help_data.get('long-summary', None)
        assert self.short_summary


class AZDevTransCommandGroup:
    # supported: 'is_preview', 'preview_info', 'is_experimental', 'experimental_info', 'operations_tmpl'

    # Ignored: 'custom_command_type', 'command_type',  'local_context_attribute', 'command_type',
    # 'custom_command_type', 'transform', 'validator', 'exception_handler', 'supports_no_wait', 'min_api', 'max_api',
    # 'resource_type', 'operation_group', 'client_factory'

    def __init__(self, name, parent_group, full_name, table_instance):
        self.name = name
        self.parent_group = parent_group
        self.full_name = full_name

        self.sub_groups = {}
        self.sub_commands = {}

        if not table_instance:
            table_instance = None

        self._parse_deprecate_info(table_instance)
        self._parse_is_preview(table_instance)
        self._parse_is_experimental(table_instance)
        assert not (self.is_preview and self.is_experimental)

        self._parse_operations_tmpl(table_instance)
        self._parse_help(table_instance)

    def _parse_deprecate_info(self, table_instance):
        if table_instance is None:
            deprecate_info = None
        else:
            deprecate_info = table_instance.group_kwargs.get('deprecate_info', None)
        if deprecate_info is not None:
            deprecate_info = AZDevTransDeprecateInfo(deprecate_info)
        self.deprecate_info = deprecate_info

    def _parse_is_preview(self, table_instance):
        if table_instance is None:
            is_preview = False
        else:
            is_preview = table_instance.group_kwargs.get('is_preview', False)
        assert isinstance(is_preview, bool)
        self.is_preview = is_preview

    def _parse_is_experimental(self, table_instance):
        if table_instance is None:
            is_experimental = False
        else:
            is_experimental = table_instance.group_kwargs.get('is_experimental', False)
        assert isinstance(is_experimental, bool)
        self.is_experimental = is_experimental

    def _parse_operations_tmpl(self, table_instance):
        if table_instance is None:
            operations_tmpl = None
        else:
            operations_tmpl = table_instance.operations_tmpl
        assert operations_tmpl is None or isinstance(operations_tmpl, str)
        self.operations_tmpl = operations_tmpl

    def _parse_help(self, table_instance):
        if table_instance is None:
            hp = None
        else:
            help_data = _load_help_file(self.full_name)
            assert help_data is not None
            hp = AZDevTransCommandGroupHelp(help_data)
        self.help = hp
