# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

def hook_azure_cli_core():
    import azure.cli.core.translator as core
    from azdev.operations.translator.hook import action
    core.cls_action_wrapper = action.cls_action_wrapper
    core.cls_action_factory_wrapper = action.cls_action_factory_wrapper

    from azdev.operations.translator.hook import arg_type
    core.register_arg_type = arg_type.register_arg_type
    core.arg_type_factory_wrapper = arg_type.arg_type_factory_wrapper

    from azdev.operations.translator.hook import client_factory
    core.func_client_factory_wrapper = client_factory.func_client_factory_wrapper

    from azdev.operations.translator.hook import completer
    core.func_completer_wrapper = completer.func_completer_wrapper
    core.completer_factory_wrapper = completer.completer_factory_wrapper
    from azure.cli.core.translator import external_completer
    external_completer._build_external_completer_instance = completer.build_external_completer_instance

    from azdev.operations.translator.hook import exception_handler
    core.func_exception_handler_wrapper = exception_handler.func_exception_handler_wrapper

    from azdev.operations.translator.hook import resource_type
    core.register_custom_resource_type = resource_type.register_custom_resource_type

    from azdev.operations.translator.hook import transformer
    core.func_transformer_wrapper = transformer.func_transformer_wrapper

    from azdev.operations.translator.hook import type_converter
    core.func_type_converter_wrapper = type_converter.func_type_converter_wrapper
    core.func_type_converter_factory_wrapper = type_converter.func_type_converter_factory_wrapper

    from azdev.operations.translator.hook import validator
    core.func_validator_wrapper = validator.func_validator_wrapper
    core.validator_factory_wrapper = validator.validator_factory_wrapper
