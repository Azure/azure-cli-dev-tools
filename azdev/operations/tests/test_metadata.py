# pylint: disable=C0301

# -----------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for
# license information.
# -----------------------------------------------------------------------------

import os
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


def compare_metadata(wheel_url, expected_metadata):
    """
    Compare metadata between wheel file and expected metadata
    """
    temp_dir = 'temp_wheels'

    try:
        # Download the wheel
        print(f"Downloading wheel from {wheel_url}")
        wheel_path = download_wheel(wheel_url, temp_dir)

        # Get metadata from wheel
        wheel_metadata = pkginfo_to_dict(wheel_path)

        # Compare metadata
        expected_metadata_cleaned = clean_metadata(expected_metadata)
        print(f"Metadata from index.json: \n{expected_metadata}")
        print(f"Metadata from index.json cleaned: \n{expected_metadata_cleaned}")
        print(f"Metadata from python wheel package: \n{wheel_metadata}")
        diff = DeepDiff(wheel_metadata, expected_metadata_cleaned, ignore_order=True)

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
        "https://azuremlsdktestpypi.blob.core.windows.net/wheels/sdk-cli-v2-public/ml-2.36.1-py3-none-any.whl",
        "https://azurecliext.blob.core.windows.net/release/azure_cli_ml-1.41.0-py3-none-any.whl"
    ]
    metadata_from_index = [
        {
            "azext.minCliCoreVersion": "2.15.0",
            "classifiers": [
                "Development Status :: 5 - Production/Stable",
                "Intended Audience :: Developers",
                "Intended Audience :: System Administrators",
                "Environment :: Console",
                "Programming Language :: Python",
                "Programming Language :: Python :: 3",
                "Programming Language :: Python :: 3.7",
                "Programming Language :: Python :: 3.8",
                "Programming Language :: Python :: 3.9",
                "Programming Language :: Python :: 3.10",
                "License :: OSI Approved :: MIT License"
            ],
            "description_content_type": "text/x-rst",
            "extensions": {
                "python.details": {
                    "contacts": [
                        {
                            "email": "azuremlsdk@microsoft.com",
                            "name": "Microsoft Corporation",
                            "role": "author"
                        }
                    ],
                    "document_names": {
                        "description": "DESCRIPTION.rst"
                    },
                    "project_urls": {
                        "Home": "https://docs.microsoft.com/azure/machine-learning/azure-machine-learning-release-notes-cli-v2?view=azureml-api-2"
                    }
                }
            },
            "extras": [],
            "generator": "bdist_wheel (0.30.0)",
            "license": "MIT",
            "metadata_version": "2.0",
            "name": "ml",
            "run_requires": [
                {
                    "requires": [
                        "azure-common (>=1.1)",
                        "azure-common>=1.1",
                        "azure-identity (==1.17.1)",
                        "azure-identity==1.17.1",
                        "azure-mgmt-resource (<23.0.0,>=3.0.0)",
                        "azure-mgmt-resource<23.0.0,>=3.0.0",
                        "azure-mgmt-resourcegraph (<9.0.0,>=2.0.0)",
                        "azure-mgmt-resourcegraph<9.0.0,>=2.0.0",
                        "azure-monitor-opentelemetry",
                        "azure-monitor-opentelemetry",
                        "azure-storage-blob (>=12.10.0)",
                        "azure-storage-blob>=12.10.0",
                        "azure-storage-file-datalake (>=12.2.0)",
                        "azure-storage-file-datalake>=12.2.0",
                        "azure-storage-file-share",
                        "azure-storage-file-share",
                        "colorama",
                        "colorama",
                        "cryptography",
                        "cryptography",
                        "docker",
                        "docker",
                        "isodate",
                        "isodate",
                        "jsonschema (>=4.0.0)",
                        "jsonschema>=4.0.0",
                        "marshmallow (>=3.5)",
                        "marshmallow>=3.5",
                        "pydash (>=6.0.0)",
                        "pydash>=6.0.0",
                        "pyjwt",
                        "pyjwt",
                        "strictyaml",
                        "strictyaml",
                        "tqdm",
                        "tqdm",
                        "typing-extensions",
                        "typing-extensions"
                    ]
                }
            ],
            "summary": "Microsoft Azure Command-Line Tools AzureMachineLearningWorkspaces Extension",
            "version": "2.36.1"
        },
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
        }
    ]

    for idx, url in enumerate(wheel_url):
        assert compare_metadata(url, metadata_from_index[idx]), "Metadata comparison failed"


if __name__ == "__main__":
    test_wheel()
