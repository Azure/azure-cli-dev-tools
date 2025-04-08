# pylint: disable=C0325,R1725,W0612,R1704,W0718,R0914,E1101,R0912,R0915,R1705

# -----------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for
# license information.
# -----------------------------------------------------------------------------

"""
Tools for generate metadata for index.json.
"""

import email.parser
import os.path
import re
import textwrap
import zipfile

from collections import OrderedDict, namedtuple

from importlib.metadata import entry_points
from packaging.requirements import Requirement  # pip install packagin

METADATA_VERSION = "2.0"

PLURAL_FIELDS = {"classifier": "classifiers",
                 "provides_dist": "provides",
                 "provides_extra": "extras"}

SKIP_FIELDS = set()

CONTACT_FIELDS = (({"email": "author_email", "name": "author"},
                   "author"),
                  ({"email": "maintainer_email", "name": "maintainer"},
                   "maintainer"))

# commonly filled out as "UNKNOWN" by distutils:
UNKNOWN_FIELDS = {"author", "author_email", "platform", "home_page", "license"}

# Wheel itself is probably the only program that uses non-extras markers
# in METADATA/PKG-INFO. Support its syntax with the extra at the end only.
EXTRA_RE = re.compile(r"""^(?P<package>.*?)(;\s*(?P<condition>.*?)(extra == '(?P<extra>.*?)')?)$""")
KEYWORDS_RE = re.compile("[\0-,]+")

MayRequiresKey = namedtuple('MayRequiresKey', ('condition', 'extra'))


class OrderedDefaultDict(OrderedDict):
    def __init__(self, *args, **kwargs):
        if not args:
            self.default_factory = None
        else:
            if not (args[0] is None or callable(args[0])):
                raise TypeError('first argument must be callable or None')
            self.default_factory = args[0]
            args = args[1:]
        super(OrderedDefaultDict, self).__init__(*args, **kwargs)

    def __missing__(self, key):
        if self.default_factory is None:
            raise KeyError(key)
        self[key] = default = self.default_factory()
        return default


def read_pkg_info(path):
    with zipfile.ZipFile(path, 'r') as zf:
        for file_name in zf.namelist():
            if file_name.endswith("METADATA"):
                with zf.open(file_name, "r") as metadata_file:
                    content = email.parser.Parser().parsestr(metadata_file.read().decode("utf-8"))
                    return content
    return {}


def unique(iterable):
    """
    Yield unique values in iterable, preserving order.
    """
    seen = set()
    for value in iterable:
        if value not in seen:
            seen.add(value)
            yield value


def handle_requires(metadata, pkg_info, key):
    """
    Place the runtime requirements from pkg_info into metadata.
    Ensures requirements are in standard format without spaces around ~=
    """
    # may_requires = DefaultDict(list)
    may_requires = OrderedDefaultDict(list)
    for value in sorted(pkg_info.get_all(key)):
        extra_match = EXTRA_RE.search(value)
        if extra_match:
            groupdict = extra_match.groupdict()
            condition = groupdict['condition']
            extra = groupdict['extra']
            package = groupdict['package']
            if condition.endswith(' and '):
                condition = condition[:-5]
        else:
            condition, extra = None, None
            package = value

        # Standardize the package requirement format by removing spaces around ~=
        if ' ~=' in package:
            package = package.replace(' ~=', '~=')

        key = MayRequiresKey(condition, extra)
        may_requires[key].append(package)

    if may_requires:
        metadata['run_requires'] = []

        def sort_key(item):
            # Both condition and extra could be None, which can't be compared
            # against strings in Python 3.
            key, value = item
            if key.condition is None:
                return ''
            return key.condition

        for key, value in sorted(may_requires.items(), key=sort_key):
            may_requirement = OrderedDict((('requires', value),))
            # may_requirement = defaultdict((('requires', value),))
            if key.extra:
                may_requirement['extra'] = key.extra
            if key.condition:
                may_requirement['environment'] = key.condition
            metadata['run_requires'].append(may_requirement)

        if 'extras' not in metadata:
            metadata['extras'] = []
        metadata['extras'].extend([key.extra for key in may_requires.keys() if key.extra])


def get_wheel_generator(whl_path):
    """
    Extract the Generator value from the WHEEL file in a .whl package.

    Args:
        whl_path (str): Path to the .whl file.

    Returns:
        str: The Generator value, or None if not found.
    """
    try:
        # Ensure the file is a valid zip file
        if not zipfile.is_zipfile(whl_path):
            print(f"The file {whl_path} is not a valid zip file.")
            return "bdist_wheel"

        # Open the .whl file
        with zipfile.ZipFile(whl_path, 'r') as zf:
            # Locate the WHEEL file
            wheel_file = None
            for file_name in zf.namelist():
                if ".dist-info/WHEEL" in file_name:
                    wheel_file = file_name
                    break

            if not wheel_file:
                print(f"WHEEL file not found in {whl_path}.")
                return "bdist_wheel"

            # Read and parse the WHEEL file
            with zf.open(wheel_file) as wf:
                for line in wf:
                    decoded_line = line.decode("utf-8").strip()
                    if decoded_line.startswith("Generator:"):
                        _, generator_value = decoded_line.split(":", 1)
                        return generator_value.strip()

            print(f"Generator key not found in {wheel_file}.")
            return "bdist_wheel"

    except Exception as e:
        print(f"An error occurred while processing {whl_path}: {e}")
        return "bdist_wheel"


def pkginfo_to_dict(path, distribution=None):
    """
    Convert PKG-INFO to a prototype Metadata 2.0 (PEP 426) dict.

    The description is included under the key ['description'] rather than
    being written to a separate file.

    path: path to wheel file
    distribution: optional distutils Distribution()
    """
    # metadata = DefaultDict(
    #     lambda: DefaultDict( lambda: DefaultDict(defaultdict)))

    metadata = OrderedDefaultDict(
        lambda: OrderedDefaultDict(lambda: OrderedDefaultDict(OrderedDict)))

    metadata["generator"] = get_wheel_generator(path)
    try:
        pkg_info = read_pkg_info(path)
    except Exception:
        with open(path, 'rb') as pkg_info_file:
            pkg_info = email.parser.Parser().parsestr(pkg_info_file.read().decode('utf-8'))

    # description = None

    if pkg_info['Summary']:
        metadata['summary'] = pkginfo_unicode(pkg_info, 'Summary')
        del pkg_info['Summary']

    # if pkg_info['Description']:
    #     description = dedent_description(pkg_info)
    #     del pkg_info['Description']
    # else:
    #     payload = pkg_info.get_payload()
    #     if isinstance(payload, bytes):
    #         # Avoid a Python 2 Unicode error.
    #         # We still suffer ? glyphs on Python 3.
    #         payload = payload.decode('utf-8')
    #     if payload:
    #         description = payload

    # if description:
    #     pkg_info['description'] = description

    for key in sorted(unique(k.lower() for k in pkg_info.keys())):
        low_key = key.replace('-', '_')

        if low_key in SKIP_FIELDS:
            continue

        if low_key in UNKNOWN_FIELDS and pkg_info.get(key) == 'UNKNOWN':
            continue

        if low_key in sorted(PLURAL_FIELDS):
            metadata[PLURAL_FIELDS[low_key]] = pkg_info.get_all(key)

        elif low_key == "requires_dist":
            handle_requires(metadata, pkg_info, key)

        elif low_key == 'provides_extra':
            if 'extras' not in metadata:
                metadata['extras'] = []
            metadata['extras'].extend(pkg_info.get_all(key))

        elif low_key == 'home_page':
            metadata['extensions']['python.details']['project_urls'] = {'Home': pkg_info[key]}

        elif low_key == 'keywords':
            metadata['keywords'] = KEYWORDS_RE.split(pkg_info[key])

        else:
            metadata[low_key] = pkg_info[key]

    metadata['metadata_version'] = METADATA_VERSION

    if 'extras' in metadata:
        metadata['extras'] = sorted(set(metadata['extras']))

    # include more information if distribution is available
    if distribution:
        for requires, attr in (('test_requires', 'tests_require'),):
            try:
                requirements = getattr(distribution, attr)
                if isinstance(requirements, list):
                    new_requirements = sorted(convert_requirements(requirements))
                    metadata[requires] = [{'requires': new_requirements}]
            except AttributeError:
                pass

    # handle contacts
    contacts = []
    for contact_type, role in CONTACT_FIELDS:
        contact = OrderedDict()
        # contact = defaultdict()
        for key in sorted(contact_type):
            if contact_type[key] in metadata:
                contact[key] = metadata.pop(contact_type[key])
        if contact:
            contact['role'] = role
            contacts.append(contact)
    if contacts:
        metadata['extensions']['python.details']['contacts'] = contacts

    # handle document_names
    # check for DESCRIPTION.rst file in the wheel package
    if zipfile.is_zipfile(path):
        with zipfile.ZipFile(path, 'r') as zf:
            for file_name in zf.namelist():
                if 'DESCRIPTION.rst' in file_name:
                    metadata['extensions']['python.details']['document_names'] = {
                        'description': 'DESCRIPTION.rst'
                    }

    # convert entry points to exports
    try:
        with open(os.path.join(os.path.dirname(path), "entry_points.txt"), "r"):
            ep_map = entry_points()
        exports = OrderedDict()
        # exports = defaultdict()
        for group, items in sorted(ep_map.items()):
            exports[group] = OrderedDict()
            # exports[group] = defaultdict()
            for item in sorted(map(str, items.values())):
                name, export = item.split(' = ', 1)
                exports[group][name] = export
        if exports:
            metadata['extensions']['python.exports'] = exports
    except IOError:
        pass

    # copy console_scripts entry points to commands
    if 'python.exports' in metadata['extensions']:
        for (ep_script, wrap_script) in (('console_scripts', 'wrap_console'),
                                         ('gui_scripts', 'wrap_gui')):
            if ep_script in metadata['extensions']['python.exports']:
                metadata['extensions']['python.commands'][wrap_script] = \
                    metadata['extensions']['python.exports'][ep_script]

    return recursive_ordered_to_dict(metadata)


def recursive_ordered_to_dict(obj):
    """
    Recursively process a data structure to convert OrderedDict and dict to sorted dict.

    Args:
        obj: The input object to process (can be OrderedDict, dict, list, or any type).

    Returns:
        dict: A dict-transformed version of the input object, with keys sorted.
    """
    if isinstance(obj, (OrderedDict, dict)):
        # Convert to dict and recursively process values, sorting keys
        return {k: recursive_ordered_to_dict(v) for k, v in sorted(obj.items())}
    elif isinstance(obj, list):
        # Recursively process each item in the list
        return [recursive_ordered_to_dict(item) for item in obj]
    else:
        # Return the object as-is for non-iterable types
        return obj


def requires_to_requires_dist(requirement):
    """Compose the version predicates for requirement in PEP 345 fashion."""
    requires_dist = []
    for op, ver in requirement.specs:
        requires_dist.append(op + ver)
    if not requires_dist:
        return ''
    return " (%s)" % ','.join(sorted(requires_dist))


def convert_requirements(requirements):
    """Yield Requires-Dist: strings for parsed requirements strings."""
    for req in requirements:
        parsed_requirement = Requirement(req)
        # parsed_requirement = pkg_resources.Requirement.parse(req)
        spec = requires_to_requires_dist(parsed_requirement)
        extras = ",".join(parsed_requirement.extras)
        if extras:
            extras = "[%s]" % extras
        yield (parsed_requirement.project_name + extras + spec)


def safe_extra(extra):
    """Mimics pkg_resources.safe_extra functionality.
    Convert an arbitrary string to a standard 'extra' name

    Any runs of non-alphanumeric characters are replaced with a single '_',
    and the result is always lowercased.
    """
    return re.sub('[^A-Za-z0-9.-]+', '_', extra).lower()


def generate_requirements(extras_require):
    """
    Convert requirements from a setup()-style dictionary to ('Requires-Dist', 'requirement')
    and ('Provides-Extra', 'extra') tuples.

    extras_require is a dictionary of {extra: [requirements]} as passed to setup(),
    using the empty extra {'': [requirements]} to hold install_requires.
    """
    for extra, depends in extras_require.items():
        condition = ''
        if extra and ':' in extra:  # setuptools extra:condition syntax
            extra, condition = extra.split(':', 1)
            extra = safe_extra(extra)
            # extra = pkg_resources.safe_extra(extra)
        if extra:
            yield ('Provides-Extra', extra)
            if condition:
                condition += " and "
            condition += "extra == '%s'" % extra
        if condition:
            condition = '; ' + condition
        for new_req in convert_requirements(depends):
            yield ('Requires-Dist', new_req + condition)


def split_sections(s):
    """Mimics pkg_resources.split_sections.

    Split a string or iterable thereof into (section, content) pairs.

    Each ``section`` is a stripped version of the section header ("[section]"),
    and each ``content`` is a list of stripped lines excluding blank lines and
    comment-only lines. If there are any such lines before the first section
    header, they're returned in a first ``section`` of ``None``.
    """

    def yield_lines(content):
        """Yields non-blank, non-comment lines from the input."""
        for line in content:
            line = line.strip()
            if line and not line.startswith("#"):
                yield line

    section = None
    content = []
    for line in yield_lines(s):
        if line.startswith("[") and line.endswith("]"):
            if section or content:
                yield section, content
            section = line[1:-1].strip()
            content = []
        elif line.startswith("[") and not line.endswith("]"):
            raise ValueError("Invalid section heading", line)
        else:
            content.append(line)

    # wrap up the last segment
    if section or content:
        yield section, content


def pkginfo_to_metadata(egg_info_path, pkginfo_path):
    """
    Convert .egg-info directory with PKG-INFO to the Metadata 1.3 aka
    old-draft Metadata 2.0 format.
    """
    pkg_info = read_pkg_info(pkginfo_path)
    pkg_info.replace_header('Metadata-Version', '2.0')
    requires_path = os.path.join(egg_info_path, 'requires.txt')
    if os.path.exists(requires_path):
        with open(requires_path) as requires_file:
            requires = requires_file.read()
        for extra, reqs in sorted(split_sections(requires), key=lambda x: x[0] or ''):
            # for extra, reqs in sorted(pkg_resources.split_sections(requires), key=lambda x: x[0] or ''):
            for item in generate_requirements({extra: reqs}):
                pkg_info[item[0]] = item[1]

    description = pkg_info['Description']
    if description:
        pkg_info.set_payload(dedent_description(pkg_info))
        del pkg_info['Description']

    return pkg_info


def pkginfo_unicode(pkg_info, field):
    """Hack to coax Unicode out of an email Message() - Python 3.3+"""
    text = pkg_info[field]
    field = field.lower()
    if not isinstance(text, str):
        if not hasattr(pkg_info, 'raw_items'):  # Python 3.2
            return str(text)
        for item in pkg_info.raw_items():
            if item[0].lower() == field:
                text = item[1].encode('ascii', 'surrogateescape') \
                    .decode('utf-8')
                break

    return text


def dedent_description(pkg_info):
    """
    Dedent and convert pkg_info['Description'] to Unicode.
    """
    description = pkg_info['Description']

    # Python 3 Unicode handling, sorta.
    surrogates = False
    if not isinstance(description, str):
        surrogates = True
        description = pkginfo_unicode(pkg_info, 'Description')

    description_lines = description.splitlines()
    description_dedent = '\n'.join(
        # if the first line of long_description is blank,
        # the first line here will be indented.
        (description_lines[0].lstrip(),
         textwrap.dedent('\n'.join(description_lines[1:])),
         '\n'))

    if surrogates:
        description_dedent = description_dedent \
            .encode("utf8") \
            .decode("ascii", "surrogateescape")

    return description_dedent


if __name__ == "__main__":
    import sys
    import pprint

    pprint.pprint(pkginfo_to_dict(sys.argv[1]))
