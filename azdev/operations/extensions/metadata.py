# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

"""
Extension metadata extraction.

Replaces the legacy wheel-0.30.0 ``metadata.json`` read path with a
``pkginfo``-based reader of the spec-compliant ``METADATA`` file inside each
extension wheel, merged with the extension's ``azext_metadata.json``.

Used by ``azdev.operations.extensions.util.get_ext_metadata`` to build the
entries stored in ``index.json``.
"""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple


# Splits a requirement string into (name, spec). Accepts both shapes that may
# appear in METADATA Requires-Dist:
#   * PEP 508 form: "oras==0.1.30"   (modern setuptools / wheel)
#   * PEP 314 form: "oras (==0.1.30)" (older setuptools, wheel 0.30.0)
# Either spec form is captured into a single, normalized spec string.
_REQ_SPLIT_RE = re.compile(
    r"^\s*(?P<name>[A-Za-z0-9_.\-]+)\s*"
    r"(?:\(\s*(?P<paren_spec>[^)]+?)\s*\)|(?P<bare_spec>[<>=!~].*?))?\s*$"
)


def _get_extension_modname(ext_dir: Path) -> str:
    pos = [d.name for d in ext_dir.iterdir() if d.is_dir() and d.name.startswith("azext_")]
    if len(pos) != 1:
        raise AssertionError(
            "Expected exactly one azext_* module in {}, found: {}".format(ext_dir, pos)
        )
    return pos[0]


def read_azext_metadata(ext_dir: Path) -> Dict[str, Any]:
    modname = _get_extension_modname(ext_dir)
    path = ext_dir / modname / "azext_metadata.json"
    if not path.is_file():
        return {}
    with path.open(encoding="utf-8") as fh:
        return json.load(fh)


def pkginfo_to_dict(ext_file) -> Dict[str, Any]:
    """Build an index.json-shaped metadata dict from a wheel file.

    This replaces the legacy ``metadata.json`` read path (which only existed
    in wheels produced by ``wheel==0.30.0``) with a ``pkginfo.Wheel`` based
    reader of the spec-defined ``METADATA`` file. Used by
    ``azdev.operations.extensions.util.get_ext_metadata``.
    """
    return merge_to_index_metadata(read_pkginfo(Path(str(ext_file))), {})


def read_pkginfo(wheel_path: Path) -> Dict[str, Any]:
    """Read spec-defined wheel metadata via pkginfo.Wheel."""
    import pkginfo

    wheel_path = Path(str(wheel_path))
    target = wheel_path
    if wheel_path.suffix != ".whl":
        import shutil
        import tempfile
        target = Path(tempfile.mkdtemp()) / (wheel_path.name + ".whl")
        shutil.copyfile(wheel_path, target)

    whl = pkginfo.Wheel(str(target))
    return {
        "name": whl.name,
        "version": whl.version,
        "summary": whl.summary,
        "description": whl.description,
        "description_content_type": whl.description_content_type,
        "license": whl.license,
        "classifiers": list(whl.classifiers or []),
        "requires_dist": list(whl.requires_dist or []),
        "requires_python": whl.requires_python,
        "author": whl.author,
        "author_email": whl.author_email,
        "home_page": whl.home_page,
        "project_urls": list(whl.project_urls or []),
        "metadata_version": whl.metadata_version,
        "keywords": whl.keywords,
    }


def _coerce_run_requires(requires_dist: List[str]) -> List[Dict[str, Any]]:
    """Approximate the legacy `run_requires` block produced by wheel 0.30.0.

    Wheel 0.30.0 emitted each requirement in two forms inside `run_requires`:
      * the PEP 314 / PEP 345 form: ``"oras (==0.1.30)"`` (name space then
        version specifier wrapped in parentheses), and
      * the canonical PEP 508 form: ``"oras==0.1.30"`` (no space, no parens).

    It also sorted entries alphabetically by package name (this is observable in
    `src/index.json`: every `run_requires` block is name-sorted regardless of
    `install_requires` order in `setup.py`).

    Modern wheel metadata (`METADATA` Requires-Dist) only carries PEP 508 and
    preserves source order, so we reproduce both transformations here.
    """
    if not requires_dist:
        return []

    parsed: List[Tuple[str, Optional[str], str]] = []
    seen: set = set()
    for req in requires_dist:
        canonical = req.strip()
        match = _REQ_SPLIT_RE.match(canonical)
        if match:
            name = match.group("name")
            spec = match.group("paren_spec") or match.group("bare_spec")
            spec = spec.strip() if spec else None
        else:
            name, spec = canonical, None
        # Older setuptools (e.g. 70.0.0) writes Requires-Dist twice per
        # package in METADATA -- once as "name (spec)" and once as
        # "name==spec". Modern setuptools writes only the canonical PEP 508
        # form. Deduplicate on (lowercase name, normalized spec) so the
        # doubling step below produces the same output regardless of which
        # setuptools generated the wheel.
        key = (name.lower(), (spec or "").replace(" ", ""))
        if key in seen:
            continue
        seen.add(key)
        parsed.append((name, spec, canonical))

    parsed.sort(key=lambda t: t[0].lower())

    doubled: List[str] = []
    for name, spec, canonical in parsed:
        if spec:
            doubled.append("{} ({})".format(name, spec))
            doubled.append("{}{}".format(name, spec))
        else:
            doubled.append(canonical)
            doubled.append(canonical)
    return [{"requires": doubled}]


def _coerce_project_urls(project_urls: List[str], home_page: Optional[str]) -> Dict[str, str]:
    out: Dict[str, str] = {}
    if home_page:
        out["Home"] = home_page
    for entry in project_urls or []:
        if "," in entry:
            label, url = entry.split(",", 1)
            out[label.strip()] = url.strip()
    return out


def _coerce_contacts(author: Optional[str], author_email: Optional[str]) -> List[Dict[str, str]]:
    if not author and not author_email:
        return []
    contact: Dict[str, str] = {"role": "author"}
    if author:
        contact["name"] = author
    if author_email:
        contact["email"] = author_email
    return [contact]


def merge_to_index_metadata(pkg: Dict[str, Any], azext: Dict[str, Any]) -> Dict[str, Any]:
    """Merge `pkginfo` output and `azext_metadata.json` into the index.json shape.

    Precedence (highest first): azext_metadata > pkginfo > derived defaults.
    """
    metadata: Dict[str, Any] = {}

    metadata["name"] = pkg.get("name")
    metadata["version"] = pkg.get("version")
    metadata["summary"] = pkg.get("summary")
    metadata["license"] = pkg.get("license")
    metadata["metadata_version"] = pkg.get("metadata_version")
    metadata["classifiers"] = pkg.get("classifiers") or []
    metadata["extras"] = []
    metadata["run_requires"] = _coerce_run_requires(pkg.get("requires_dist") or [])
    metadata["requires_python"] = pkg.get("requires_python")
    metadata["description_content_type"] = pkg.get("description_content_type")

    contacts = _coerce_contacts(pkg.get("author"), pkg.get("author_email"))
    project_urls = _coerce_project_urls(pkg.get("project_urls") or [], pkg.get("home_page"))
    details: Dict[str, Any] = {}
    if contacts:
        details["contacts"] = contacts
    if project_urls:
        details["project_urls"] = project_urls
    if details:
        metadata["extensions"] = {"python.details": details}

    metadata.update(azext)

    return {k: v for k, v in metadata.items() if v is not None}
