""""Compiling of C++."""

from distutils.sysconfig import get_python_inc
import pathlib
import subprocess
import typing as t

import argunparse
from static_typing.ast_manipulation import RecursiveAstVisitor
# import typed_ast.ast3 as typed_ast3

from ..general import Language, CodeReader, Parser, AstGeneralizer, Unparser, Compiler

PYTHON_LIB_PATH = pathlib.Path(get_python_inc(plat_specific=1))

SWIG_INTERFACE_TEMPLATE = '''/* File: {module_name}.i */
%module {module_name}

%{
#define SWIG_FILE_WITH_INIT
{include_directives}
%}

{function_signatures}
'''


class SwigCompiler(Compiler):

    """SWIG-based compiler."""

    def __init__(self, language: Language):
        super().__init__()
        self.language = language
        self.argunparser = argunparse.ArgumentUnparser()

    def create_swig_interface(self, path: pathlib.Path) -> str:
        code_reader = CodeReader()
        parser = Parser.find(self.language)()
        ast_generalizer = AstGeneralizer.find(self.language)()
        unparser = Unparser.find(self.language)(headers=True)
        code = code_reader.read_file(path)
        cpp_tree = parser.parse(code, path)
        tree = ast_generalizer.generalize(cpp_tree)
        tree
        from horast import ast_

        module_name = path.with_extension('').name
        include_directives = ['#include {}'.format('<cstdlib>')]
        function_signatures = ['int add(int a, int b);']
        swig_interface = SWIG_INTERFACE_TEMPLATE.format(
            module_name=module_name, include_directives='\n'.join(include_directives),
            function_signatures='\n'.join(function_signatures))

    def run_swig(self, interface_path: pathlib.Path, *args) -> subprocess.CompletedProcess:
        # $ swig -python example.i
        # If building a C++ extension, add the -c++ option:
        # $ swig -c++ -python example.i
        swig_cmd = ['swig', '-python']
        swig_cmd += args
        swig_cmd.append(str(interface_path))
        result = subprocess.run(swig_cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        return result


class CppSwigCompiler(SwigCompiler):

    """SWIG-based compiler for C++."""

    def __init__(self):
        super().__init__(Language.find('C++'))

    def run_gpp(self, path: pathlib.Path, wrapper_path: pathlib.Path = None):
        # gcc -c example.c example_wrap.c -I/usr/local/include/python2.1
        gcc_cmd = ['gcc', '-c', str(path), str(wrapper_path), '-I{}'.format(PYTHON_LIB_PATH)]
        result = subprocess.run(gcc_cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        return result

    def run_ld(self, path: pathlib.Path, wrapper_path: pathlib.Path = None):
        # ld -shared example.o example_wrap.o -o _example.so
        ld_cmd = ['ld', '-shared', str(path.with_suffix('.o')), str(wrapper_path.with_suffix('.o')),
                  '-o', '_{}'.format(path.with_suffix('.so'))]
        result = subprocess.run(ld_cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        return result

    def compile(self, code: str, path: t.Optional[pathlib.Path] = None,
                output_folder: t.Optional[pathlib.Path] = None, *args, **kwargs) -> pathlib.Path:
        swig_interface = self.create_swig_interface(path)
        swig_interface_path = path.with_suffix('.i')
        with open(str(), 'w') as swig_interface_file:
            swig_interface_file.write(swig_interface)
        self.run_swig(swig_interface_path, '-c++')
        cpp_path = path.with_suffix('.cpp')
        wrapper_path = cpp_path.with_name(cpp_path.with_suffix('').name + '_wrap')
        self.run_gpp(cpp_path, wrapper_path)
        self.run_ld(cpp_path, wrapper_path)
