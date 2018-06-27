"""Below code is generic boilerplate and normally should not be changed.

To avoid setup script boilerplate, create "setup.py" file with the following minimal contents
and modify them according to the specifics of your package.

See the implementation of setup_boilerplate.Package for default metadata values and available
options.
"""

import importlib
import pathlib
import sys
import typing as t

import docutils.nodes
import docutils.parsers.rst
import docutils.utils
import setuptools

__updated__ = '2018-04-18'

SETUP_TEMPLATE = '''"""Setup script."""

import setup_boilerplate


class Package(setup_boilerplate.Package):

    """Package metadata."""

    name = ''
    description = ''
    download_url = 'https://github.com/mbdevpl/...'
    classifiers = [
        'Development Status :: 1 - Planning',
        'Programming Language :: Python :: 3.4',
        'Programming Language :: Python :: 3.5',
        'Programming Language :: Python :: 3.6',
        'Programming Language :: Python :: 3 :: Only']
    keywords = []


if __name__ == '__main__':
    Package.setup()
'''

HERE = pathlib.Path(__file__).resolve().parent


def find_version(
        package_name: str, version_module_name: str = '_version',
        version_variable_name: str = 'VERSION') -> str:
    """Simulate behaviour of "from package_name._version import VERSION", and return VERSION."""
    version_module = importlib.import_module(
        '{}.{}'.format(package_name.replace('-', '_'), version_module_name))
    return getattr(version_module, version_variable_name)


def find_packages(root_directory: str = '.') -> t.List[str]:
    """Find packages to pack."""
    exclude = ['test', 'test.*'] if ('bdist_wheel' in sys.argv or 'bdist' in sys.argv) else []
    packages_list = setuptools.find_packages(root_directory, exclude=exclude)
    return packages_list


def parse_requirements(
        requirements_path: str = 'requirements.txt') -> t.List[str]:
    """Read contents of requirements.txt file and return data from its relevant lines.

    Only non-empty and non-comment lines are relevant.
    """
    requirements = []
    with HERE.joinpath(requirements_path).open() as reqs_file:
        for requirement in [line.strip() for line in reqs_file.read().splitlines()]:
            if not requirement or requirement.startswith('#'):
                continue
            requirements.append(requirement)
    return requirements


def partition_version_classifiers(
        classifiers: t.Sequence[str], version_prefix: str = 'Programming Language :: Python :: ',
        only_suffix: str = ' :: Only') -> t.Tuple[t.List[str], t.List[str]]:
    """Find version number classifiers in given list and partition them into 2 groups."""
    versions_min, versions_only = [], []
    for classifier in classifiers:
        version = classifier.replace(version_prefix, '')
        versions = versions_min
        if version.endswith(only_suffix):
            version = version.replace(only_suffix, '')
            versions = versions_only
        try:
            versions.append(tuple([int(_) for _ in version.split('.')]))
        except ValueError:
            pass
    return versions_min, versions_only


def find_required_python_version(
        classifiers: t.Sequence[str], version_prefix: str = 'Programming Language :: Python :: ',
        only_suffix: str = ' :: Only') -> t.Optional[str]:
    """Determine the minimum required Python version."""
    versions_min, versions_only = partition_version_classifiers(
        classifiers, version_prefix, only_suffix)
    if len(versions_only) > 1:
        raise ValueError(
            'more than one "{}" version encountered in {}'.format(only_suffix, versions_only))
    only_version = None
    if len(versions_only) == 1:
        only_version = versions_only[0]
        for version in versions_min:
            if version[:len(only_version)] != only_version:
                raise ValueError(
                    'the "{}" version {} is inconsistent with version {}'
                    .format(only_suffix, only_version, version))
    min_supported_version = None
    for version in versions_min:
        if min_supported_version is None or \
                (len(version) >= len(min_supported_version) and version < min_supported_version):
            min_supported_version = version
    if min_supported_version is None:
        if only_version is not None:
            return '.'.join([str(_) for _ in only_version])
    else:
        return '>=' + '.'.join([str(_) for _ in min_supported_version])
    return None


def parse_rst(text: str) -> docutils.nodes.document:
    """Parse text assuming it's an RST markup."""
    parser = docutils.parsers.rst.Parser()
    components = (docutils.parsers.rst.Parser,)
    settings = docutils.frontend.OptionParser(components=components).get_default_values()
    document = docutils.utils.new_document('<rst-doc>', settings=settings)
    parser.parse(text, document)
    return document


class SimpleRefCounter(docutils.nodes.NodeVisitor):

    """Find all simple references in a given docutils document."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.references = []

    def visit_reference(self, node: docutils.nodes.reference) -> None:
        """Called for "reference" nodes."""
        if len(node.children) != 1 or not isinstance(node.children[0], docutils.nodes.Text) \
                or not all(_ in node.attributes for _ in ('name', 'refuri')):
            return
        path = pathlib.Path(node.attributes['refuri'])
        try:
            if path.is_absolute():
                return
            resolved_path = path.resolve()
        except FileNotFoundError:  # in resolve(), prior to Python 3.6
            return
        except OSError:  # in is_absolute() and resolve(), on URLs in Windows
            return
        try:
            resolved_path.relative_to(HERE)
        except ValueError:
            return
        if not path.is_file():
            return
        assert node.attributes['name'] == node.children[0].astext()
        self.references.append(node)

    def unknown_visit(self, node: docutils.nodes.Node) -> None:
        """Called for unknown node types."""
        pass


def resolve_relative_rst_links(text: str, base_link: str):
    """Resolve all relative links in a given RST document.

    All links of form `link`_ become `link <base_link/link>`_.
    """
    document = parse_rst(text)
    visitor = SimpleRefCounter(document)
    document.walk(visitor)
    for target in visitor.references:
        name = target.attributes['name']
        uri = target.attributes['refuri']
        new_link = '`{} <{}{}>`_'.format(name, base_link, uri)
        if name == uri:
            text = text.replace('`<{}>`_'.format(uri), new_link)
        else:
            text = text.replace('`{} <{}>`_'.format(name, uri), new_link)
    return text


class Package:

    """Default metadata and behaviour for a Python package setup script."""

    root_directory = '.'  # type: str
    """Root directory of the source code of the package, relative to the setup.py file location."""

    name = None  # type: str

    version = None  # type: str
    """"If None, it will be obtained from "package_name._version.VERSION" variable."""

    description = None  # type: str

    long_description = None  # type: str
    """If None, it will be generated from readme."""

    url = 'https://mbdevpl.github.io/'  # type: str
    download_url = 'https://github.com/mbdevpl'  # type: str
    author = 'Mateusz Bysiek'  # type: str
    author_email = 'mb@mbdev.pl'  # type: str
    # maintainer = None  # type: str
    # maintainer_email = None  # type: str
    license_str = 'Apache License 2.0'  # type: str

    classifiers = []  # type: t.List[str]
    """List of valid project classifiers: https://pypi.python.org/pypi?:action=list_classifiers"""

    keywords = []  # type: t.List[str]

    packages = None  # type: t.List[str]
    """If None, determined with help of setuptools."""

    package_data = {}
    exclude_package_data = {}

    install_requires = None  # type: t.List[str]
    """If None, determined using requirements.txt."""

    extras_require = {}  # type: t.Mapping[str, t.List[str]]
    """A dictionary containing entries of type 'some_feature': ['requirement1', 'requirement2']."""

    python_requires = None  # type: str
    """If None, determined from provided classifiers."""

    entry_points = {}  # type: t.Mapping[str, t.List[str]]
    """A dictionary used to enable automatic creation of console scripts, gui scripts and plugins.

    Example entry:
    'console_scripts': ['script_name = package.subpackage:function']
    """

    test_suite = 'test'  # type: str

    @classmethod
    def try_fields(cls, *names) -> t.Optional[t.Any]:
        """Return first existing of given class field names."""
        for name in names:
            if hasattr(cls, name):
                return getattr(cls, name)
        raise AttributeError((cls, names))

    @classmethod
    def parse_readme(cls, readme_path: str = 'README.rst', encoding: str = 'utf-8') -> str:
        """Parse readme and resolve relative links in it if it is feasible.

        Links are resolved if readme is in rst format and the package is hosted on GitHub.
        """
        with HERE.joinpath(readme_path).open(encoding=encoding) as readme_file:
            long_description = readme_file.read()  # type: str

        if readme_path.endswith('.rst') and cls.download_url.startswith('https://github.com/'):
            base_url = '{}/blob/v{}/'.format(cls.download_url, cls.version)
            long_description = resolve_relative_rst_links(long_description, base_url)

        return long_description

    @classmethod
    def prepare(cls) -> None:
        """Fill in possibly missing package metadata."""
        if cls.version is None:
            cls.version = find_version(cls.name)
        if cls.long_description is None:
            cls.long_description = cls.parse_readme()
        if cls.packages is None:
            cls.packages = find_packages(cls.root_directory)
        if cls.install_requires is None:
            cls.install_requires = parse_requirements()
        if cls.python_requires is None:
            cls.python_requires = find_required_python_version(cls.classifiers)

    @classmethod
    def setup(cls) -> None:
        """Run setuptools.setup() with correct arguments."""
        cls.prepare()
        setuptools.setup(
            name=cls.name, version=cls.version, description=cls.description,
            long_description=cls.long_description, url=cls.url, download_url=cls.download_url,
            author=cls.author, author_email=cls.author_email,
            maintainer=cls.try_fields('maintainer', 'author'),
            maintainer_email=cls.try_fields('maintainer_email', 'author_email'),
            license=cls.license_str, classifiers=cls.classifiers, keywords=cls.keywords,
            packages=cls.packages, package_dir={'': cls.root_directory},
            include_package_data=True,
            package_data=cls.package_data, exclude_package_data=cls.exclude_package_data,
            install_requires=cls.install_requires, extras_require=cls.extras_require,
            python_requires=cls.python_requires,
            entry_points=cls.entry_points, test_suite=cls.test_suite)
