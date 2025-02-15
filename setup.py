"""Setup script for transpyle package."""

import setup_boilerplate


class Package(setup_boilerplate.Package):
    """Package metadata."""

    name = 'transpyle'
    description = 'performance-oriented transpiler for Python'
    url = 'https://github.com/mbdevpl/transpyle'
    classifiers = [
        'Development Status :: 2 - Pre-Alpha',
        'Environment :: Console',
        'Intended Audience :: Developers',
        'Intended Audience :: Science/Research',
        'License :: OSI Approved :: Apache Software License',
        'Natural Language :: English',
        'Operating System :: MacOS :: MacOS X',
        'Operating System :: POSIX :: Linux',
        'Programming Language :: Python :: 3.5',
        'Programming Language :: Python :: 3.6',
        'Programming Language :: Python :: 3.7',
        'Programming Language :: Python :: 3 :: Only',
        'Topic :: Education',
        'Topic :: Scientific/Engineering',
        'Topic :: Software Development :: Code Generators',
        'Topic :: Software Development :: Compilers',
        'Topic :: Software Development :: Pre-processors',
        'Topic :: Utilities']
    keywords = ['compiler', 'just-in-time', 'source-to-source', 'transpilation', 'transpiler']
    extras_require = {
        'all': setup_boilerplate.parse_requirements('requirements_all.txt'),
        'c': setup_boilerplate.parse_requirements('requirements_c.txt'),
        'cpp': setup_boilerplate.parse_requirements('requirements_cpp.txt'),
        'cython': setup_boilerplate.parse_requirements('requirements_cython.txt'),
        'fortran': setup_boilerplate.parse_requirements('requirements_fortran.txt'),
        'opencl': setup_boilerplate.parse_requirements('requirements_opencl.txt')}
    entry_points = {'console_scripts': ['transpyle = transpyle.__main__:main']}


if __name__ == '__main__':
    Package.setup()
