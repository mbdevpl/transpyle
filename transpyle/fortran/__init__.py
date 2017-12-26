"""Fortran parsing/unparsing support for transpyle package."""

from ..general import Language, Parser, AstGeneralizer, Unparser, Compiler, Binder
from .parser import FortranParser
from .ast_generalizer import FortranAstGeneralizer
from .unparser import Fortran77Unparser, Fortran2008Unparser
from .compiler import F2PyCompiler
from .binder import F2PyBinder


Language.register(Language(['Fortran 77'], ['.f']), ['Fortran 77'])
Language.register(Language(['Fortran 95'], ['.f90', '.f', '.for', '.f95']), ['Fortran 95'])
# Language.register(Language(['Fortran 2003'], ['.f90', '.f', '.for', '.f95']), ['Fortran 2003'])
Language.register(Language(['Fortran 2008'], ['.f90', '.f', '.for', '.f95']),
                  ['Fortran 2008', 'Fortran'])

Parser.register(FortranParser, (Language.find('Fortran 77'), Language.find('Fortran 95'),
                                Language.find('Fortran 2008')))

AstGeneralizer.register(FortranAstGeneralizer,
                        (Language.find('Fortran 77'), Language.find('Fortran 95'),
                         Language.find('Fortran 2008')))

Unparser.register(Fortran77Unparser, (Language.find('Fortran 77'),))
Unparser.register(Fortran2008Unparser, (Language.find('Fortran 95'), Language.find('Fortran 2008')))

Compiler.register(F2PyCompiler, (Language.find('Fortran 77'), Language.find('Fortran 95'),
                                 Language.find('Fortran 2008')))

Binder.register(F2PyBinder, (Language.find('Fortran 77'), Language.find('Fortran 95'),
                             Language.find('Fortran 2008')))
