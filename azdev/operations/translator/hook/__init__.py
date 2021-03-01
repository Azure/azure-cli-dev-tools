# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

def hook_azure_cli_core():
    import azure.cli.core.translator as core
    from azdev.operations.translator.hook import action
    core.action_class = action.action_class
    core.action_class_by_factory = action.action_class_by_factory

    from azdev.operations.translator.hook import arg_type
    core.register_arg_type = arg_type.register_arg_type
    core.arg_type_by_factory = arg_type.arg_type_by_factory

    from azdev.operations.translator.hook import client_factory
    core.client_factory_func = client_factory.client_factory_func

    from azdev.operations.translator.hook import completer
    core.completer_func = completer.completer_func
    core.completer_by_factory = completer.completer_by_factory
    from azure.cli.core.translator import external_completer
    external_completer._build_external_completer_instance = completer.build_external_completer_instance

    from azdev.operations.translator.hook import exception_handler
    core.exception_handler_func = exception_handler.exception_handler_func

    from azdev.operations.translator.hook import resource_type
    core.register_custom_resource_type = resource_type.register_custom_resource_type

    from azdev.operations.translator.hook import transformer
    core.transformer_func = transformer.transformer_func

    from azdev.operations.translator.hook import type_converter
    core.type_converter_func = type_converter.type_converter_func
    core.type_converter_by_factory = type_converter.type_converter_by_factory

    from azdev.operations.translator.hook import validator
    core.validator_func = validator.validator_func
    core.validator_by_factory = validator.validator_by_factory
