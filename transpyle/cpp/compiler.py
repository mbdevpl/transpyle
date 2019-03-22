""""Compiling of C++."""

from distutils.sysconfig import get_python_inc, get_config_vars
import logging
import pathlib
import platform
import shutil
import subprocess
import tempfile
import typing as t

import argunparse
import numpy as np
# from static_typing.ast_manipulation import RecursiveAstVisitor
# import typed_ast.ast3 as typed_ast3

from ..general import Language, CodeReader, Parser, AstGeneralizer, Unparser, Compiler
from ..general.tools import temporarily_change_dir, run_tool

PYTHON_LIB_PATH = pathlib.Path(get_python_inc(plat_specific=1))

PYTHON_CONFIG = get_config_vars()

SWIG_INTERFACE_TEMPLATE = '''/* File: {module_name}.i */
/* Generated by transpyle. */
%module {module_name}

%{{
#define SWIG_FILE_WITH_INIT
{include_directives}
%}}

%include "numpy.i"

%init %{{
import_array();
%}}

// %include "std_valarray.i";
%include "std_vector.i";

namespace std {{
    %template(valarray_double) valarray<double>;
    %template(vector_double) vector<double>;
}}

{function_signatures}
'''

SWIG_INTERFACE_TEMPLATE_HPP = '''/* File: {module_name}.i */
/* Generated by transpyle. */
%module {module_name}

%{{
#define SWIG_FILE_WITH_INIT
#include "{include_path}"
%}}

%include "numpy.i"

%init %{{
import_array();
%}}

// %include "std_valarray.i";
%include "std_list.i";
%include "std_vector.i";
// %include "std_array.i";
%include "std_set.i";
%include "std_map.i";

namespace std {{
//    %template(valarray_double) valarray<double>;
//    %template(array_double) array<double>;
    %template(vector_double) vector<double>;
}}

%include "{include_path}"

// below is Python 3 support, however,
// adding it will generate wrong .so file
// for Fedora 25 on ARMv7. So be sure to
// comment them when you compile for
// Fedora 25 on ARMv7.
%begin %{{
#define SWIG_PYTHON_STRICT_BYTE_CHAR
%}}
'''

TRANSPYLE_CPP_RESOURCES_PATH = pathlib.Path('./resources/cpp/').resolve()

_LOG = logging.getLogger(__name__)


class CompilerInterface(Compiler):

    compiler_steps = []  # type: t.List[t.Any]

    def compile(self, code: str, path: t.Optional[pathlib.Path] = None,
                output_folder: t.Optional[pathlib.Path] = None, **kwargs) -> pathlib.Path:

        for compiler_step in self.compiler_steps:
            compiler_step(path, )


def split_and_strip(text: str) -> t.List[str]:
    return tuple([_.strip() for _ in text.split() if _.strip()])


class CppCompilerInterface:

    executable = None  # type: str

    flags = ('-O3', '-fPIC', '-fopenmp')

    compiler_flags = tuple(split_and_strip('{} {}'.format(
        PYTHON_CONFIG['BASECFLAGS'], PYTHON_CONFIG['BASECPPFLAGS'])))

    linker_flags = ()

    include_paths = [
        pathlib.Path(PYTHON_CONFIG['INCLUDEPY']),
        *[pathlib.Path(_, 'core', 'include') for _ in np.__path__]]

    library_paths = [
        pathlib.Path(PYTHON_CONFIG['LIBDIR'])]

    compiler_flags = split_and_strip('{} {}'.format(
        PYTHON_CONFIG['BASECFLAGS'], PYTHON_CONFIG['BASECPPFLAGS']))

    ldlibrary = pathlib.Path(PYTHON_CONFIG['LDLIBRARY'].lstrip('lib')).with_suffix('')

    libraries = split_and_strip('-l{} {} {} {}'.format(
        ldlibrary, PYTHON_CONFIG['LIBS'], PYTHON_CONFIG['SYSLIBS'], PYTHON_CONFIG['LINKFORSHARED']))

    # linker_flags = split_and_strip('-L{} -l{} {} {} {}'.format(
    #     PYTHON_CONFIG['LIBDIR'], ldlibrary, PYTHON_CONFIG['LIBS'],
    #     PYTHON_CONFIG['SYSLIBS'], PYTHON_CONFIG['LINKFORSHARED']))

    @property
    def compiler_options(self):
        return [*self.flags, *self.compiler_flags, *['-I{}'.format(_) for _ in self.include_paths]]

    @property
    def linker_options(self):
        return [*self.flags, *self.linker_flags, *['-L{}'.format(_) for _ in self.library_paths],
                *self.libraries]

    def compile(self, input_paths: t.Sequence[pathlib.Path]) -> subprocess.CompletedProcess:
        return run_tool(pathlib.Path(self.executable), [
            *self.compiler_options, '-c', *[str(path) for path in input_paths]])

    def link(self, input_paths: t.Sequence[pathlib.Path],
             output_path: pathlib.Path) -> subprocess.CompletedProcess:
        return run_tool(pathlib.Path(self.executable), [
            *self.linker_options, '-shared', *[str(path) for path in input_paths],
            '-o', str(output_path)])

    def compile_and_link(self, input_paths: t.Sequence[pathlib.Path], output_path: pathlib.Path):
        compiler_result = self.compile(input_paths)
        # assert compiler_result.returncode == 0
        linker_result = self.link([path.with_suffix('.o') for path in input_paths], output_path)
        # assert linker_result.returncode == 0
        return compiler_result, linker_result


class GppInterface(CppCompilerInterface):

    """Use GNU compiler suite for compiling C++."""

    executable = 'g++'


class ClangppInterface(CppCompilerInterface):

    """Use clang for compiling C++."""

    executable = 'clang++'


class SwigCompiler(Compiler):

    """SWIG-based compiler."""

    def __init__(self, language: Language):
        super().__init__()
        self.language = language
        self.argunparser = argunparse.ArgumentUnparser()

    def create_header_file(self, path: pathlib.Path) -> str:
        """Create a header for a given C/C++ source code file."""
        code_reader = CodeReader()
        parser = Parser.find(self.language)()
        ast_generalizer = AstGeneralizer.find(self.language)({'path': path})
        unparser = Unparser.find(self.language)(headers=True)
        code = code_reader.read_file(path)
        cpp_tree = parser.parse(code, path)
        tree = ast_generalizer.generalize(cpp_tree)
        header_code = unparser.unparse(tree)
        _LOG.debug('unparsed raw header file: """%s"""', header_code)
        return header_code

    def _create_swig_interface(self, path: pathlib.Path) -> str:
        """Create a SWIG interface for a given C/C++ source code file."""
        module_name = path.with_suffix('').name
        header_code = self.create_header_file(path)
        include_directives = []
        function_signatures = []
        for line in header_code.splitlines():
            if line.startswith('#include'):
                collection = include_directives
            else:
                collection = function_signatures
            collection.append(line)
        swig_interface = SWIG_INTERFACE_TEMPLATE.format(
            module_name=module_name, include_directives='\n'.join(include_directives),
            function_signatures='\n'.join(function_signatures))
        _LOG.debug('SWIG interface: """%s"""', swig_interface)
        return swig_interface

    def create_swig_interface(self, path: pathlib.Path) -> str:
        """Create a SWIG interface for a given C/C++ header file."""
        module_name = path.with_suffix('').name
        swig_interface = SWIG_INTERFACE_TEMPLATE_HPP.format(
            module_name=module_name, include_path=path)
        _LOG.debug('SWIG interface: """%s"""', swig_interface)
        return swig_interface

    def run_swig(self, interface_path: pathlib.Path, *args) -> subprocess.CompletedProcess:
        """Run SWIG.

        For C extensions:
        swig -python example.i

        If building a C++ extension, add the -c++ option:
        swig -c++ -python example.i
        """
        swig_cmd = ['swig', '-I{}'.format(TRANSPYLE_CPP_RESOURCES_PATH),
                    '-python', *args, str(interface_path)]
        _LOG.info('running SWIG via %s', swig_cmd)
        return run_tool(pathlib.Path(swig_cmd[0]), swig_cmd[1:])


class CppSwigCompiler(SwigCompiler):

    """SWIG-based compiler for C++."""

    # py_config = get_config_vars()
    # cpp_flags = ('-O3', '-fPIC', '-fopenmp')

    def __init__(self):
        super().__init__(Language.find('C++'))
        self.cpp_compiler = {'Linux': GppInterface(),
                             'Darwin': ClangppInterface()}[platform.system()]

    # def run_gpp(self, *args) -> subprocess.CompletedProcess:
    #     compiler = {'Linux': 'g++', 'Darwin': 'clang++'}[platform.system()]
    #     gcc_cmd = [compiler, *args]
    #     _LOG.warning('running C++ compiler: %s', gcc_cmd)
    #     return run_tool(pathlib.Path(compiler), args)

    # def run_cpp_compiler(self, path: pathlib.Path,
    #                      wrapper_path: pathlib.Path = None) -> subprocess.CompletedProcess:
    #     # gcc -c example.c example_wrap.c -I/usr/local/include/python2.1
    #     flags = '-I{} {} {}'.format(
    #         self.py_config['INCLUDEPY'],
    #         self.py_config['BASECFLAGS'], self.py_config['BASECPPFLAGS']).split()
    #     flags = [_.strip() for _ in flags if _.strip()]
    #     gcc_args = [*self.cpp_flags, *flags,
    #                 '-c', str(path), str(wrapper_path)]
    #     return self.run_gpp(*gcc_args)

    # def run_cpp_linker(self, path: pathlib.Path,
    #                    wrapper_path: pathlib.Path = None) -> subprocess.CompletedProcess:
    #     # ld -shared example.o example_wrap.o -o _example.so
    #     ldlibrary = pathlib.Path(self.py_config['LDLIBRARY'].lstrip('lib')).with_suffix('')
    #     flags = '-L{} -l{} {} {} {}'.format(
    #         self.py_config['LIBDIR'], ldlibrary, self.py_config['LIBS'],
    #         self.py_config['SYSLIBS'], self.py_config['LINKFORSHARED']).split()
    #     flags = [_.strip() for _ in flags if _.strip()]
    #     linker_args = [*self.cpp_flags, *flags,
    #                    '-shared', str(path.with_suffix('.o')), str(wrapper_path.with_suffix('.o')),
    #                    '-o', '{}'.format(path.with_name('_' + path.name).with_suffix('.so'))]
    #     return self.run_gpp(*linker_args)

    def compile(self, code: str, path: t.Optional[pathlib.Path] = None,
                output_folder: t.Optional[pathlib.Path] = None, **kwargs) -> pathlib.Path:
        if output_folder is None:
            with tempfile.TemporaryDirectory() as tmpdir:
                output_folder = pathlib.Path(tmpdir)
            output_folder.mkdir()
        header_code = self.create_header_file(path)
        hpp_path = output_folder.joinpath(path.name).with_suffix('.hpp')
        with hpp_path.open('w') as header_file:
            header_file.write(header_code)
        swig_interface = self.create_swig_interface(hpp_path.relative_to(output_folder))
        cpp_path = output_folder.joinpath(path.name)
        shutil.copy2(str(path), str(cpp_path))
        swig_interface_path = output_folder.joinpath(path.with_suffix('.i').name)
        with swig_interface_path.open('w') as swig_interface_file:
            swig_interface_file.write(swig_interface)
        wrapper_path = output_folder.joinpath(path.with_suffix('').name + '_wrap.cxx')

        # shutil.copy2(str(pathlib.Path('./resources/cpp/numpy.i')), str(output_folder.joinpath('numpy.i')))

        with temporarily_change_dir(output_folder):
            result = self.run_swig(swig_interface_path, '-c++')
            if result.returncode != 0:
                raise RuntimeError('{} -- Failed to create SWIG interface for "{}":\n"""\n{}"""\n'
                                   'The header "{}" is:\n"""{}"""\nExamine folder "{}" for details'
                                   .format(result.args, path, result.stderr.decode(), hpp_path,
                                           header_code, output_folder))

            # gcc -c example.c example_wrap.c -I/usr/local/include/python2.1
            # ld -shared example.o example_wrap.o -o _example.so
            compiler_result, linker_result = self.cpp_compiler.compile_and_link(
                [cpp_path, wrapper_path], cpp_path.with_name('_' + cpp_path.name).with_suffix('.so'))
            assert compiler_result.returncode == 0
            assert linker_result.returncode == 0

            # result = self.run_cpp_compiler(cpp_path, wrapper_path)
            # assert result.returncode == 0
            # result = self.run_cpp_linker(cpp_path, wrapper_path)
            # assert result.returncode == 0

        return cpp_path.with_suffix('.py')
