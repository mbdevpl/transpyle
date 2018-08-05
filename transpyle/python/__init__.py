"""Python support for transpyle package."""

import datetime
import inspect
import logging
import pathlib
import tempfile
import types
import typing as t

import typed_ast.ast3 as typed_ast3

from ..pair import make_range_call, make_numpy_constructor, make_st_ndarray
from ..general import \
    CodeReader, Language, Parser, AstGeneralizer, IdentityAstGeneralizer, Unparser, Translator, \
    AutoTranspiler, Binder
from .parser import TypedPythonParserWithComments
from .unparser import TypedPythonUnparserWithComments
from .translator import PythonTranslator
from .transformations import inline

_LOG = logging.getLogger(__name__)

Language.register(Language(['Python 3.5'], ['.py']), ['Python 3.5'])
Language.register(Language(['Python 3.6'], ['.py']), ['Python 3.6', 'Python 3', 'Python'])

Parser.register(TypedPythonParserWithComments,
                (Language.find('Python 3.5'), Language.find('Python 3.6')))


class PythonAstGeneralizer(IdentityAstGeneralizer):

    """Python doesn't need AST generalizer."""

    pass


AstGeneralizer.register(PythonAstGeneralizer,
                        (Language.find('Python 3.5'), Language.find('Python 3.6')))

Unparser.register(TypedPythonUnparserWithComments,
                  (Language.find('Python 3.5'), Language.find('Python 3.6')))

Translator.register(PythonTranslator, (Language.find('Python 3.5'), Language.find('Python 3.6')))


def transpile(function_or_class, to_language: Language, *args, **kwargs):
    """Instantiate Python transpiler to transpile one function or class.

    Meant to be used as decorator."""
    if not isinstance(function_or_class, types.FunctionType):
        raise NotImplementedError('transpiler only supports pure Python user-defined functions now')
    transpiler = AutoTranspiler(Language.find('Python 3'), to_language)
    function_or_class_code = CodeReader.read_function(function_or_class)
    path = inspect.getsourcefile(function_or_class)
    if path is not None:
        path = pathlib.Path(path)
    compile_path = pathlib.Path(tempfile.gettempdir(), 'transpyle_{}_{}_tmp_{}'.format(
        function_or_class.__name__, to_language.default_name.replace(' ', '_'),
        datetime.datetime.now().strftime('%Y%m%d%H%M%S%f')))
    compile_path.mkdir(parents=True)
    translated_path = pathlib.Path(compile_path,
                                   path.with_suffix(to_language.default_file_extension).name)
    _LOG.warning('compiling code translated to %s into %s', to_language, compile_path)
    compiled_path = transpiler.transpile(
        function_or_class_code, path, translated_path, compile_path)
    module = Binder().bind(compiled_path)
    interface = getattr(module, function_or_class.__name__)
    return interface
