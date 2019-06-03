# coding=utf-8
# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from knack.help_files import helps  # pylint: disable=unused-import


# TODO: Replace OBJECT and OBJECTS placeholders with your preferred descriptors.
helps['{{ name }}'] = """
    type: group
    short-summary: Commands to manage OBJECT.
"""

helps['{{ name }} create'] = """
    type: command
    short-summary: Create a OBJECT.
"""

helps['{{ name }} list'] = """
    type: command
    short-summary: List OBJECTS.
"""
{% if sdk_path %}
helps['{{ name }} delete'] = """
    type: command
    short-summary: Delete a OBJECT.
"""

helps['{{ name }} show'] = """
    type: command
    short-summary: Show details of a OBJECT.
"""

helps['{{ name }} update'] = """
    type: command
    short-summary: Update a OBJECT.
"""
{% else %}
# helps['{{ name }} delete'] = """
#     type: command
#     short-summary: Delete a OBJECT.
# """

# helps['{{ name }} show'] = """
#     type: command
#     short-summary: Show details of a OBJECT.
# """

# helps['{{ name }} update'] = """
#     type: command
#     short-summary: Update a OBJECT.
# """
{% endif %}