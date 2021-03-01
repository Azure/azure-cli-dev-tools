# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
from azdev.operations.translator.utilities import AZDevTransNode


class AZDevTransExceptionHandler(AZDevTransNode):
    key = 'exception-handler'

    def __init__(self, exception_handler):
        from azdev.operations.translator.hook.exception_handler import AZExceptionHandler
        if not isinstance(exception_handler, AZExceptionHandler):
            raise TypeError('Exception handler is not an instance of "AzExceptionHandler", get "{}"'.format(
                type(exception_handler)))
        self.exception_handler = exception_handler

    def to_config(self, ctx):
        raise NotImplementedError()


class AZDevTransExceptionHandlerFunc(AZDevTransExceptionHandler):

    def __init__(self, exception_handler):
        from azdev.operations.translator.hook.exception_handler import AZExceptionHandlerFunc
        if not isinstance(exception_handler, AZExceptionHandlerFunc):
            raise TypeError('Exception handler is not an instance of "AzFuncExceptionHandler", get "{}"'.format(
                type(exception_handler)))
        super(AZDevTransExceptionHandlerFunc, self).__init__(exception_handler)
        self.import_module = exception_handler.import_module
        self.import_name = exception_handler.import_name

    def to_config(self, ctx):
        value = ctx.get_import_path(self.import_module, self.import_name)
        return self.key, value


def build_exception_handler(exception_handler):
    from azdev.operations.translator.hook.exception_handler import AZExceptionHandler, AZExceptionHandlerFunc
    if exception_handler is None:
        return None
    if not isinstance(exception_handler, AZExceptionHandler):
        raise TypeError('Exception handler is not an instance of "AzExceptionHandler", get "{}"'.format(
            type(exception_handler)))
    if isinstance(exception_handler, AZExceptionHandlerFunc):
        return AZDevTransExceptionHandlerFunc(exception_handler)
    else:
        raise NotImplementedError()
