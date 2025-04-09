# pylint: disable=C0301

# -----------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for
# license information.
# -----------------------------------------------------------------------------

import json
import os
import re
import zipfile
import requests

from deepdiff import DeepDiff
from azdev.operations.extensions.metadata import pkginfo_to_dict


def download_wheel(url, dest_dir):
    """
    Download wheel file from URL to destination directory
    """
    if not os.path.exists(dest_dir):
        os.makedirs(dest_dir)

    filename = os.path.basename(url)
    dest_path = os.path.join(dest_dir, filename)

    response = requests.get(url)
    response.raise_for_status()

    with open(dest_path, 'wb') as f:
        f.write(response.content)

    return dest_path


def clean_metadata(original_metadata):
    """
    Remove specified keys from the metadata.
    :param original_metadata: Original metadata
    :return: Cleaned metadata
    """
    keys_to_remove = {
        "azext.isPreview",
        "azext.minCliCoreVersion",
        "azext.isExperimental",
        "azext.isExprimental",
        "azext.maxCliCoreVersion"
    }
    return {k: v for k, v in original_metadata.items() if k not in keys_to_remove}


# copy from wheel==0.30.0
WHEEL_INFO_RE = re.compile(
    r"""^(?P<namever>(?P<name>.+?)(-(?P<ver>\d.+?))?)
    ((-(?P<build>\d.*?))?-(?P<pyver>.+?)-(?P<abi>.+?)-(?P<plat>.+?)
    \.whl|\.dist-info)$""",
    re.VERBOSE).match


def _get_extension_modname(ext_dir):
    # Modification of https://github.com/Azure/azure-cli/blob/dev/src/azure-cli-core/azure/cli/core/extension.py#L153
    EXTENSIONS_MOD_PREFIX = 'azext_'
    pos_mods = [n for n in os.listdir(ext_dir)
                if n.startswith(EXTENSIONS_MOD_PREFIX) and os.path.isdir(os.path.join(ext_dir, n))]
    if len(pos_mods) != 1:
        raise AssertionError("Expected 1 module to load starting with "
                             "'{}': got {}".format(EXTENSIONS_MOD_PREFIX, pos_mods))
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


def get_ext_metadata(ext_dir, ext_file, ext_name):
    generated_metadata = pkginfo_to_dict(ext_file)
    print(f"generated_metadata from python wheel package: \n{generated_metadata}")

    with zipfile.ZipFile(ext_file, 'r') as zip_ref:
        zip_ref.extractall(ext_dir)

    metadata = {}
    # dist_info_dirs = [f for f in os.listdir(ext_dir) if f.endswith('.dist-info')]

    azext_metadata = _get_azext_metadata(ext_dir)
    print(f"azext_metadata from python wheel package: \n{azext_metadata}")

    if not azext_metadata:
        raise ValueError('azext_metadata.json for Extension "{}" Metadata is missing'.format(ext_name))

    metadata.update(azext_metadata)

    metadata.update(generated_metadata)
    # for dist_info_dirname in dist_info_dirs:
    #     parsed_dist_info_dir = WHEEL_INFO_RE(dist_info_dirname)
    #     if parsed_dist_info_dir and parsed_dist_info_dir.groupdict().get('name') == ext_name.replace('-', '_'):
    #         metadata.update(generated_metadata)
    return metadata


def compare_metadata(wheel_url, expected_metadata):
    """
    Compare metadata between wheel file and expected metadata
    """
    temp_dir = 'temp_wheels'

    try:
        print(f"Metadata from index.json: \n{expected_metadata}")
        # Download the wheel
        print(f"Downloading wheel from {wheel_url}")
        ext_file = download_wheel(wheel_url, temp_dir)
        ext_name = os.path.basename(wheel_url)

        # Get metadata from wheel
        wheel_metadata = get_ext_metadata(temp_dir, ext_file, ext_name)

        # Compare metadata
        print(f"Metadata from python wheel package: \n{wheel_metadata}")
        diff = DeepDiff(expected_metadata, wheel_metadata, ignore_order=True)

        if diff:
            print("Metadata mismatch found:")
            print(f"Differences:\n{diff}")
            return False

        print("Metadata built from python wheel package matches metadata from index.json.")
        return True

    finally:
        # Cleanup
        if os.path.exists(temp_dir):
            import shutil
            shutil.rmtree(temp_dir)


def test_wheel():
    """
    Test specific wheel metadata consistency
    """
    wheel_url = [
        "https://azurecliext.blob.core.windows.net/release/azure_cli_ml-1.41.0-py3-none-any.whl",
        "https://azurecliprod.blob.core.windows.net/cli-extensions/alias-0.5.2-py2.py3-none-any.whl"
    ]
    metadata_from_index = [
        {
            "azext.minCliCoreVersion": "2.3.1",
            "classifiers": [
                "Development Status :: 3 - Alpha",
                "Intended Audience :: Developers",
                "Intended Audience :: System Administrators",
                "Programming Language :: Python :: 3.5",
                "Programming Language :: Python :: 3.6",
                "Programming Language :: Python :: 3.7",
                "Programming Language :: Python :: 3.8",
                "Programming Language :: Python :: 3.9"
            ],
            "description_content_type": "text/x-rst",
            "extensions": {
                "python.details": {
                    "contacts": [
                        {
                            "email": "azpycli@microsoft.com",
                            "name": "Microsoft Corporation",
                            "role": "author"
                        }
                    ],
                    "document_names": {
                        "description": "DESCRIPTION.rst",
                        "license": "LICENSE.txt"
                    },
                    "project_urls": {
                        "Home": "https://docs.microsoft.com/python/api/overview/azure/ml/?view=azure-ml-py"
                    }
                }
            },
            "extras": [],
            "generator": "bdist_wheel (0.30.0)",
            "license": "Proprietary https://aka.ms/azureml-preview-sdk-license ",
            "metadata_version": "2.0",
            "name": "azure-cli-ml",
            "requires_python": ">=3.5,<4",
            "run_requires": [
                {
                    "requires": [
                        "adal (>=1.2.1)",
                        "azureml-cli-common (~=1.41)",
                        "cryptography (<=3.3.2)",
                        "docker (>=3.7.2)",
                        "msrest (>=0.6.6)",
                        "pyyaml (>=5.1.0)",
                        "requests (>=2.21.0)"
                    ]
                }
            ],
            "summary": "Microsoft Azure Command-Line Tools AzureML Command Module",
            "version": "1.41.0"
        },
        {
            "azext.isPreview": True,
            "azext.minCliCoreVersion": "2.0.50.dev0",
            "classifiers": [
                "Development Status :: 4 - Beta",
                "Intended Audience :: Developers",
                "Intended Audience :: System Administrators",
                "Programming Language :: Python",
                "Programming Language :: Python :: 2",
                "Programming Language :: Python :: 2.7",
                "Programming Language :: Python :: 3",
                "Programming Language :: Python :: 3.4",
                "Programming Language :: Python :: 3.5",
                "Programming Language :: Python :: 3.6",
                "License :: OSI Approved :: MIT License"
            ],
            "extensions": {
                "python.details": {
                    "contacts": [
                        {
                            "email": "t-chwong@microsoft.com",
                            "name": "Ernest Wong",
                            "role": "author"
                        }
                    ],
                    "document_names": {
                        "description": "DESCRIPTION.rst"
                    },
                    "project_urls": {
                        "Home": "https://github.com/Azure/azure-cli-extensions"
                    }
                }
            },
            "extras": [],
            "generator": "bdist_wheel (0.30.0)",
            "license": "MIT",
            "metadata_version": "2.0",
            "name": "alias",
            "run_requires": [
                {
                    "requires": [
                        "jinja2 (~=2.10)"
                    ]
                }
            ],
            "summary": "Support for command aliases",
            "version": "0.5.2"
        }
    ]

    for idx, url in enumerate(wheel_url):
        assert compare_metadata(url, metadata_from_index[idx]), "Metadata comparison failed"


if __name__ == "__main__":
    test_wheel()
