# -----------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for
# license information.
# -----------------------------------------------------------------------------

import json
import importlib.util
import os
import sys
import tempfile
import unittest
import zipfile
from pathlib import Path

_TEST_DIR = os.path.abspath(os.path.dirname(__file__))
_UTIL_PATH = os.path.abspath(os.path.join(_TEST_DIR, "..", "extensions", "util.py"))
_UTIL_SPEC = importlib.util.spec_from_file_location("extensions_util_under_test", _UTIL_PATH)
_UTIL_MODULE = importlib.util.module_from_spec(_UTIL_SPEC)
assert _UTIL_SPEC and _UTIL_SPEC.loader
sys.modules[_UTIL_SPEC.name] = _UTIL_MODULE
_UTIL_SPEC.loader.exec_module(_UTIL_MODULE)

_METADATA_PATH = os.path.abspath(os.path.join(_TEST_DIR, "..", "extensions", "metadata.py"))
_METADATA_SPEC = importlib.util.spec_from_file_location("extensions_metadata_under_test", _METADATA_PATH)
_METADATA_MODULE = importlib.util.module_from_spec(_METADATA_SPEC)
assert _METADATA_SPEC and _METADATA_SPEC.loader
sys.modules[_METADATA_SPEC.name] = _METADATA_MODULE
_METADATA_SPEC.loader.exec_module(_METADATA_MODULE)

get_ext_metadata = _UTIL_MODULE.get_ext_metadata
get_pkg_info_from_pkg_metafile = _UTIL_MODULE.get_pkg_info_from_pkg_metafile

_coerce_run_requires = getattr(_METADATA_MODULE, "_coerce_run_requires")  # pylint: disable=protected-access
read_azext_metadata = _METADATA_MODULE.read_azext_metadata
merge_to_index_metadata = _METADATA_MODULE.merge_to_index_metadata


def _write_json(path, payload):
    with open(path, "w", encoding="utf-8") as f:
        json.dump(payload, f)


def _build_test_wheel(path, dist_info_dir):
    """Build a minimal valid wheel readable by ``pkginfo.Wheel``.

    The wheel embeds an ``azext_metadata.json`` inside the extension module and
    a spec-compliant ``METADATA`` file. The legacy ``metadata.json`` artifact
    is intentionally omitted, mirroring modern setuptools/wheel output.
    """
    with zipfile.ZipFile(path, "w") as zf:
        zf.writestr(
            "azext_demo/azext_metadata.json",
            json.dumps({"azext.isPreview": True, "summary": "from_azext"}),
        )
        zf.writestr(
            dist_info_dir + "/METADATA",
            "Metadata-Version: 2.1\n"
            "Name: demo-ext\n"
            "Version: 0.1.0\n"
            "Summary: from_wheel\n"
            "License: MIT\n"
            "Requires-Dist: foo==1.0.0\n",
        )
        zf.writestr(dist_info_dir + "/WHEEL", "Wheel-Version: 1.0\nGenerator: test\n")


class MetadataUtilTestCase(unittest.TestCase):

    def test_get_ext_metadata_merges_azext_and_wheel_metadata(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            wheel_path = os.path.join(temp_dir, "demo_ext-0.1.0-py3-none-any.whl")
            _build_test_wheel(wheel_path, "demo_ext-0.1.0.dist-info")

            extract_dir = os.path.join(temp_dir, "extract")
            os.makedirs(extract_dir, exist_ok=True)

            metadata = get_ext_metadata(
                ext_dir=extract_dir,
                ext_file=wheel_path,
                ext_name="demo-ext",
            )

            # pkginfo-derived metadata overrides duplicated azext fields
            self.assertEqual("from_wheel", metadata.get("summary"))
            self.assertEqual(True, metadata.get("azext.isPreview"))
            self.assertEqual(
                [{"requires": ["foo (==1.0.0)", "foo==1.0.0"]}],
                metadata.get("run_requires"),
            )
            self.assertEqual("demo-ext", metadata.get("name"))
            self.assertEqual("0.1.0", metadata.get("version"))

    def test_get_ext_metadata_preserves_azext_only_fields(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            wheel_path = os.path.join(temp_dir, "demo_ext-0.1.0-py3-none-any.whl")
            _build_test_wheel(wheel_path, "demo_ext-0.1.0.dist-info")

            extract_dir = os.path.join(temp_dir, "extract")
            os.makedirs(extract_dir, exist_ok=True)

            metadata = get_ext_metadata(
                ext_dir=extract_dir,
                ext_file=wheel_path,
                ext_name="demo-ext",
            )

            # azext-only namespace keys must survive the merge
            self.assertEqual(True, metadata.get("azext.isPreview"))

    def test_get_pkg_info_from_pkg_metafile_reads_name_and_version(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            pkg_info_path = os.path.join(temp_dir, "PKG-INFO")
            with open(pkg_info_path, "w", encoding="utf-8") as f:
                f.write("Metadata-Version: 2.1\n")
                f.write("Name: demo-ext\n")
                f.write("Version: 1.2.3\n")

            pkg_info = get_pkg_info_from_pkg_metafile(pkg_info_path)

            self.assertEqual("demo-ext", pkg_info.get("pkg_name"))
            self.assertEqual("1.2.3", pkg_info.get("pkg_version"))


class MetadataModuleTestCase(unittest.TestCase):

    def test_coerce_run_requires_dedups_and_sorts_pep314_and_pep508(self):
        requires_dist = [
            "zlib==1.2.11",
            "oras (==0.1.30)",
            "oras==0.1.30",
        ]

        result = _coerce_run_requires(requires_dist)

        self.assertEqual(
            [{"requires": [
                "oras (==0.1.30)",
                "oras==0.1.30",
                "zlib (==1.2.11)",
                "zlib==1.2.11",
            ]}],
            result,
        )

    def test_read_azext_metadata_reads_module_metadata_file(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            ext_dir = Path(temp_dir)
            mod_dir = ext_dir / "azext_demo"
            mod_dir.mkdir(parents=True, exist_ok=True)
            metadata_file = mod_dir / "azext_metadata.json"
            metadata_file.write_text(json.dumps({"azext.isPreview": True}), encoding="utf-8")

            result = read_azext_metadata(ext_dir)
            self.assertEqual({"azext.isPreview": True}, result)

    def test_merge_to_index_metadata_azext_overrides_pkg(self):
        pkg = {
            "name": "demo-ext",
            "version": "0.1.0",
            "summary": "pkg-summary",
            "license": "MIT",
            "metadata_version": "2.4",
            "classifiers": ["Development Status :: 4 - Beta"],
            "requires_dist": ["oras==0.1.30"],
            "author": "Author A",
            "author_email": "author@example.com",
            "home_page": "https://example.com",
            "project_urls": ["Docs, https://example.com/docs"],
        }
        azext = {
            "summary": "azext-summary",
            "azext.isPreview": True,
        }

        result = merge_to_index_metadata(pkg, azext)

        self.assertEqual("azext-summary", result.get("summary"))
        self.assertEqual(True, result.get("azext.isPreview"))
        self.assertEqual([{"requires": ["oras (==0.1.30)", "oras==0.1.30"]}], result.get("run_requires"))

    def test_merge_to_index_metadata_maps_pyproject_homepage_to_home(self):
        """A pyproject package has no Home-page; its `[project.urls] Homepage`
        must still land under the `Home` label the index has always used."""
        pkg = {
            "name": "demo-ext",
            "version": "0.1.0",
            "home_page": None,
            "project_urls": [
                "Homepage, https://example.com",
                "Docs, https://example.com/docs",
            ],
        }

        result = merge_to_index_metadata(pkg, {})

        project_urls = result["extensions"]["python.details"]["project_urls"]
        self.assertEqual("https://example.com", project_urls["Home"])
        self.assertEqual("https://example.com/docs", project_urls["Docs"])
        self.assertNotIn("Homepage", project_urls)

    def test_merge_to_index_metadata_setup_py_home_page_still_wins(self):
        """A setup.py package keeps using Home-page, and it takes precedence."""
        pkg = {
            "name": "demo-ext",
            "version": "0.1.0",
            "home_page": "https://from-home-page.example.com",
            "project_urls": ["Homepage, https://from-project-url.example.com"],
        }

        result = merge_to_index_metadata(pkg, {})

        project_urls = result["extensions"]["python.details"]["project_urls"]
        self.assertEqual("https://from-home-page.example.com", project_urls["Home"])

    def test_merge_to_index_metadata_falls_back_to_license_expression(self):
        """PEP 639 wheels carry License-Expression instead of License."""
        pkg = {
            "name": "demo-ext",
            "version": "0.1.0",
            "license": None,
            "license_expression": "MIT",
        }

        result = merge_to_index_metadata(pkg, {})

        self.assertEqual("MIT", result.get("license"))
        self.assertEqual("demo-ext", result.get("name"))


pkginfo_to_dict = _METADATA_MODULE.pkginfo_to_dict


_GOLDEN_EXCLUDE_PATHS = {
    "root['generator']",                                              # bdist_wheel banner
    "root['metadata_version']",                                       # 2.0 vs 2.1/2.4
    "root['extensions']['python.details']['document_names']",         # wheel 0.30.0 only
    "root['test_requires']",                                          # dropped from modern METADATA
    # METADATA 2.0 wheels lack description_content_type; wheel 0.30.0
    # surfaced it via the side-channel metadata.json.
    "root['description_content_type']",
}


def _clean_golden(metadata):
    """Normalize legacy index.json metadata for comparison against pkginfo output.

    - Drops ``azext.*`` keys (those are merged in by ``get_ext_metadata`` from
      the extension's ``azext_metadata.json``, not by ``pkginfo_to_dict``).
    - Strips trailing whitespace from the ``license`` string (pkginfo does so).
    """
    cleaned = {k: v for k, v in metadata.items() if not k.startswith("azext.")}
    if isinstance(cleaned.get("license"), str):
        cleaned["license"] = cleaned["license"].strip()
    return cleaned


_GOLDEN_FIXTURES = [
    {
        "url": "https://azcliprod.blob.core.windows.net/cli-extensions/azure_cli_ml-1.41.0-py3-none-any.whl",
        "ext_name": "azure-cli-ml",
        "metadata": {
            "azext.minCliCoreVersion": "2.3.1",
            "classifiers": [
                "Development Status :: 3 - Alpha",
                "Intended Audience :: Developers",
                "Intended Audience :: System Administrators",
                "Programming Language :: Python :: 3.5",
                "Programming Language :: Python :: 3.6",
                "Programming Language :: Python :: 3.7",
                "Programming Language :: Python :: 3.8",
                "Programming Language :: Python :: 3.9",
            ],
            "description_content_type": "text/x-rst",
            "extensions": {
                "python.details": {
                    "contacts": [
                        {
                            "email": "azpycli@microsoft.com",
                            "name": "Microsoft Corporation",
                            "role": "author",
                        }
                    ],
                    "project_urls": {
                        "Home": "https://docs.microsoft.com/python/api/overview/azure/ml/?view=azure-ml-py"
                    },
                },
            },
            "extras": [],
            "license": "Proprietary https://aka.ms/azureml-preview-sdk-license ",
            "name": "azure-cli-ml",
            "requires_python": ">=3.5,<4",
            "run_requires": [
                {
                    "requires": [
                        "adal (>=1.2.1)",
                        "adal>=1.2.1",
                        "azureml-cli-common (~=1.41)",
                        "azureml-cli-common~=1.41",
                        "cryptography (<=3.3.2)",
                        "cryptography<=3.3.2",
                        "docker (>=3.7.2)",
                        "docker>=3.7.2",
                        "msrest (>=0.6.6)",
                        "msrest>=0.6.6",
                        "pyyaml (>=5.1.0)",
                        "pyyaml>=5.1.0",
                        "requests (>=2.21.0)",
                        "requests>=2.21.0",
                    ]
                }
            ],
            "summary": "Microsoft Azure Command-Line Tools AzureML Command Module",
            "version": "1.41.0",
        },
    },
]


class MetadataGoldenComparisonTestCase(unittest.TestCase):
    """End-to-end check: pkginfo_to_dict output matches historical index.json."""

    @classmethod
    def _download(cls, url, dest_path):
        import requests  # local import; only needed when this test runs

        response = requests.get(url, timeout=30)
        response.raise_for_status()
        with open(dest_path, "wb") as fh:
            fh.write(response.content)

    def _compare(self, fixture):
        try:
            from deepdiff import DeepDiff
        except ImportError as exc:
            self.skipTest("deepdiff not installed: {}".format(exc))

        with tempfile.TemporaryDirectory() as temp_dir:
            wheel_path = os.path.join(temp_dir, os.path.basename(fixture["url"]))
            try:
                self._download(fixture["url"], wheel_path)
            except Exception as exc:  # pylint: disable=broad-exception-caught  # network/blob outage, 404, etc.
                self.skipTest("could not download {}: {}".format(fixture["url"], exc))

            generated = pkginfo_to_dict(wheel_path)
            golden = _clean_golden(fixture["metadata"])

            diff = DeepDiff(
                golden,
                generated,
                ignore_order=True,
                exclude_paths=_GOLDEN_EXCLUDE_PATHS,
            )
            self.assertFalse(
                diff,
                msg="metadata for {} diverged from index.json golden:\n{}".format(
                    fixture["ext_name"], diff
                ),
            )

    def test_pkginfo_metadata_matches_index_json(self):
        for fixture in _GOLDEN_FIXTURES:
            with self.subTest(extension=fixture["ext_name"]):
                self._compare(fixture)


if __name__ == "__main__":
    unittest.main()
