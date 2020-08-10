# -----------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for
# license information.
# -----------------------------------------------------------------------------


def performance_benchmark_data_transformer(result):
    from collections import OrderedDict

    output = []

    for r in result:
        item = OrderedDict()
        item["Command"] = r["Command"]
        item["Min"] = r["Min"]
        item["Avg"] = r["Avg"]
        item["Max"] = r["Max"]
        item["Media"] = r["Media"]
        item["Std"] = r["Std"]
        output.append(item)

    return output
