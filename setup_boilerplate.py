"""Below code is generic boilerplate and normally should not be changed.

To avoid setup script boilerplate, create "setup.py" file with the following minimal contents
and modify them according to the specifics of your package.

See the implementation of setup_boilerplate.Package for default metadata values and available
options.
"""

import importlib
import pathlib
import shutil
import sys
import typing as t

import setuptools

__updated__ = '2017-09-04'

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


def parse_readme(readme_path: str = 'README.rst', encoding: str = 'utf-8') -> str:
    """Read contents of readme file (by default "README.rst") and return them."""
    with open(str(HERE.joinpath(readme_path)), encoding=encoding) as readme_file:
        desc = readme_file.read()
    return desc


def parse_requirements(
        requirements_path: str = 'requirements.txt') -> t.List[str]:
    """Read contents of requirements.txt file and return data from its relevant lines.

    Only non-empty and non-comment lines are relevant.
    """
    requirements = []
    with open(str(HERE.joinpath(requirements_path))) as reqs_file:
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


class Package:

    """Default metadata and behaviour for a Python package setup script."""

    root_directory = '.' # type: str
    """Root directory of the source code of the package, relative to the setup.py file location."""

    name = None # type: str
    description = None # type: str
    url = 'https://mbdevpl.github.io/' # type: str
    download_url = 'https://github.com/mbdevpl' # type: str
    author = 'Mateusz Bysiek' # type: str
    author_email = 'mb@mbdev.pl' # type: str
    # maintainer = None # type: str
    # maintainer_email = None # type: str
    license_str = 'Apache License 2.0' # type: str

    classifiers = [] # type: t.List[str]
    """List of valid project classifiers: https://pypi.python.org/pypi?:action=list_classifiers"""

    keywords = [] # type: t.List[str]
    package_data = {}
    exclude_package_data = {}

    extras_require = {} # type: t.Mapping[str, t.List[str]]
    """A dictionary containing entries of type 'some_feature': ['requirement1', 'requirement2']."""

    entry_points = {} # type: t.Mapping[str, t.List[str]]
    """A dictionary used to enable automatic creation of console scripts, gui scripts and plugins.

    Example entry:
    'console_scripts': ['script_name = package.subpackage:function']
    """

    test_suite = 'test' # type: str

    @classmethod
    def try_fields(cls, *names) -> t.Optional[t.Any]:
        for name in names:
            if hasattr(cls, name):
                return getattr(cls, name)

    @classmethod
    def clean(cls, build_directory_name: str = 'build') -> None:
        """Recursively delete build directory (by default "build") if it exists."""
        build_directory_path = pathlib.Path(HERE, build_directory_name)
        if build_directory_path.is_dir():
            shutil.rmtree(str(build_directory_path))

    @classmethod
    def setup(cls) -> None:
        """Run setuptools.setup() with correct arguments."""
        setuptools.setup(
            name=cls.name, version=find_version(cls.name), description=cls.description,
            long_description=parse_readme(), url=cls.url, download_url=cls.download_url,
            author=cls.author, author_email=cls.author_email,
            maintainer=cls.try_fields('maintainer', 'author'),
            maintainer_email=cls.try_fields('maintainer_email', 'author_email'),
            license=cls.license_str, classifiers=cls.classifiers, keywords=cls.keywords,
            packages=find_packages(cls.root_directory), package_dir={'': cls.root_directory},
            include_package_data=True,
            package_data=cls.package_data, exclude_package_data=cls.exclude_package_data,
            install_requires=parse_requirements(), extras_require=cls.extras_require,
            python_requires=find_required_python_version(cls.classifiers),
            entry_points=cls.entry_points, test_suite=cls.test_suite
            )
