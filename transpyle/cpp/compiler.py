""""Compiling of C++."""

from distutils.sysconfig import get_python_inc
import logging
import os
import pathlib
import shutil
import subprocess
import typing as t

import argunparse
# from static_typing.ast_manipulation import RecursiveAstVisitor
# import typed_ast.ast3 as typed_ast3

from ..general import Language, CodeReader, Parser, AstGeneralizer, Unparser, Compiler

PYTHON_LIB_PATH = pathlib.Path(get_python_inc(plat_specific=1))

SWIG_INTERFACE_TEMPLATE = '''/* File: {module_name}.i */
%module {module_name}

%{{
#define SWIG_FILE_WITH_INIT
{include_directives}
%}}

{function_signatures}
'''

_LOG = logging.getLogger(__name__)


class SwigCompiler(Compiler):

    """SWIG-based compiler."""

    def __init__(self, language: Language):
        super().__init__()
        self.language = language
        self.argunparser = argunparse.ArgumentUnparser()

    def create_swig_interface(self, path: pathlib.Path) -> str:
        """Create a SWIG interface file for a given C/C++ source code file."""
        code_reader = CodeReader()
        parser = Parser.find(self.language)()
        ast_generalizer = AstGeneralizer.find(self.language)({'path': path})
        unparser = Unparser.find(self.language)(headers=True)
        code = code_reader.read_file(path)
        cpp_tree = parser.parse(code, path)
        tree = ast_generalizer.generalize(cpp_tree)
        header_code = unparser.unparse(tree)
        _LOG.warning('unparsed raw header file: """%s"""', header_code)

        include_directives = []
        function_signatures = []
        for line in header_code.splitlines():
            if line.startswith('#include'):
                collection = include_directives
            else:
                collection = function_signatures
            collection.append(line)

        module_name = path.with_suffix('').name
        swig_interface = SWIG_INTERFACE_TEMPLATE.format(
            module_name=module_name, include_directives='\n'.join(include_directives),
            function_signatures='\n'.join(function_signatures))
        return swig_interface

    def run_swig(self, interface_path: pathlib.Path, *args) -> subprocess.CompletedProcess:
        """Run SWIG.

        For C extensions:
        swig -python example.i

        If building a C++ extension, add the -c++ option:
        swig -c++ -python example.i
        """
        swig_cmd = ['swig', '-python', *args, str(interface_path)]
        _LOG.warning('running %s', swig_cmd)
        result = subprocess.run(swig_cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        _LOG.warning('result is %s', result)
        return result


class CppSwigCompiler(SwigCompiler):

    """SWIG-based compiler for C++."""

    def __init__(self):
        super().__init__(Language.find('C++'))

    def run_gpp(self, path: pathlib.Path, wrapper_path: pathlib.Path = None):
        # gcc -c example.c example_wrap.c -I/usr/local/include/python2.1
        gcc_cmd = ['g++', '-c', str(path), str(wrapper_path), '-I{}'.format(PYTHON_LIB_PATH),
                   '-fPIC']
        _LOG.warning('running %s', gcc_cmd)
        result = subprocess.run(gcc_cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        return result

    def run_ld(self, path: pathlib.Path, wrapper_path: pathlib.Path = None):
        # ld -shared example.o example_wrap.o -o _example.so
        ld_cmd = ['ld', '-shared', str(path.with_suffix('.o')), str(wrapper_path.with_suffix('.o')),
                  '-o', '_{}'.format(path.with_suffix('.so'))]
        _LOG.warning('running %s', ld_cmd)
        result = subprocess.run(ld_cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        _LOG.warning('result is %s', result)
        return result

    def compile(self, code: str, path: t.Optional[pathlib.Path] = None,
                output_folder: t.Optional[pathlib.Path] = None, **kwargs) -> pathlib.Path:
        swig_interface = self.create_swig_interface(path)
        cpp_path = output_folder.joinpath(path.name)
        shutil.copy2(path, cpp_path)
        swig_interface_path = output_folder.joinpath(path.with_suffix('.i').name)
        with swig_interface_path.open('w') as swig_interface_file:
            swig_interface_file.write(swig_interface)
        wrapper_path = output_folder.joinpath(path.with_suffix('').name + '_wrap.cxx')

        cwd = os.getcwd()
        os.chdir(str(output_folder))
        result = self.run_swig(swig_interface_path, '-c++')
        assert result.returncode == 0, result
        result = self.run_gpp(cpp_path, wrapper_path)
        assert result.returncode == 0, result
        result = self.run_ld(cpp_path, wrapper_path)
        assert result.returncode == 0, result
        os.chdir(cwd)
        return cpp_path
