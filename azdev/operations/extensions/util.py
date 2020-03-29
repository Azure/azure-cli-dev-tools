# -----------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for
# license information.
# -----------------------------------------------------------------------------

import os
import json
import re
import zipfile

from pkginfo import Wheel
from knack.util import CLIError

from azdev.utilities import EXTENSION_PREFIX


WHEEL_INFO_RE = re.compile(
    r"""^(?P<namever>(?P<name>.+?)(-(?P<ver>\d.+?))?)
    ((-(?P<build>\d.*?))?-(?P<pyver>.+?)-(?P<abi>.+?)-(?P<plat>.+?)
    \.whl|\.dist-info)$""",
    re.VERBOSE).match


def _get_extension_modname(ext_dir):
    # Modification of https://github.com/Azure/azure-cli/blob/dev/src/azure-cli-core/azure/cli/core/extension.py#L153
    pos_mods = [n for n in os.listdir(ext_dir)
                if n.startswith(EXTENSION_PREFIX) and os.path.isdir(os.path.join(ext_dir, n))]
    if len(pos_mods) != 1:
        raise AssertionError("Expected 1 module to load starting with "
                             "'{}': got {}".format(EXTENSION_PREFIX, pos_mods))
    return pos_mods[0]


def _get_azext_metadata(ext_dir):
    # Modification of https://github.com/Azure/azure-cli/blob/dev/src/azure-cli-core/azure/cli/core/extension.py#L109
    AZEXT_METADATA_FILENAME = 'azext_metadata.json'
    azext_metadata = None
    ext_modname = _get_extension_modname(ext_dir=ext_dir)
    azext_metadata_filepath = os.path.join(ext_dir, ext_modname, AZEXT_METADATA_FILENAME)
    if os.path.isfile(azext_metadata_filepath):
        with open(azext_metadata_filepath) as f:
            azext_metadata = json.load(f)
    return azext_metadata


def get_ext_metadata(ext_dir, ext_file):
    zip_ref = zipfile.ZipFile(ext_file, 'r')
    zip_ref.extractall(ext_dir)
    zip_ref.close()
    metadata = {}
    azext_metadata = _get_azext_metadata(ext_dir)
    if azext_metadata:
        metadata.update(azext_metadata)

    try:
        ext_wheel = Wheel(ext_file)

        t = vars(ext_wheel)
        del t['filename']
        del t['description']    # del as line too long

        metadata.update(vars(ext_wheel))
    except ValueError:
        raise CLIError('{} is not a valid wheel'.format(ext_file))

    return metadata


def get_whl_from_url(url, filename, tmp_dir, whl_cache=None):
    print('-' * 20, 'get_whl_from_url', '-' * 20)
    print(filename)

    if not whl_cache:
        whl_cache = {}
    if url in whl_cache:
        return whl_cache[url]
    import requests
    r = requests.get(url, stream=True)
    try:
        assert r.status_code == 200, "Request to {} failed with {}".format(url, r.status_code)
    except AssertionError:
        raise CLIError("unable to download (status code {}): {}".format(r.status_code, url))
    ext_file = os.path.join(tmp_dir, filename)
    with open(ext_file, 'wb') as f:
        for chunk in r.iter_content(chunk_size=1024):
            if chunk:  # ignore keep-alive new chunks
                f.write(chunk)
    whl_cache[url] = ext_file
    return ext_file
