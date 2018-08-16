"""Commandline utility for transpyle package."""

import argparse
import pathlib
import sys

import ordered_set
import pandas as pd

from .general import Language, CodeReader, CodeWriter, AutoTranslator
from .general import Parser, AstGeneralizer, Unparser, Compiler, Binder

PROG_NAME = 'transpyle'
COPYRIGHT_NOTICE = 'Copyright 2017-2018 Mateusz Bysiek https://mbdevpl.github.io/,' \
    ' Apache License 2.0'
STEP_DESCRIPTIONS = {
    'parsing':
    'transforming code in a specific programming language into language-specific AST',
    'generalization':
    'transforming language-specific AST into generalized and extended Python AST',
    'unparsing':
    'transforming generalized and extended Python AST into code in a specific programming'
    ' language',
    'compiling':
    'transforming source code in a specific programming language into compiled binary',
    'binding': 'creating a callable Python object for a compiled library'}


def query_registry() -> pd.DataFrame:
    """Gather information about supported languages in transpyle and scope of their support."""
    classes = (Parser, AstGeneralizer, Unparser, Compiler, Binder)
    distinct_languages = list(ordered_set.OrderedSet(Language.registered.values()))
    language_support = {}
    for language in distinct_languages:
        language_support[language] = [cls.find(language) is not None for cls in classes]
    return pd.DataFrame(columns=classes, index=distinct_languages,
                        data=[support for _, support in language_support.items()], dtype=bool)


def show_supported_langs():
    support_data = query_registry()
    support_data = pd.DataFrame(
        columns=[cls.__name__ for cls in support_data.columns],
        index=[language.default_name for language in support_data.index],
        data=[['✓' if support else '' for support in data_row]
              for _, data_row in support_data.iterrows()], dtype=str)
    print(support_data.to_string(header=list(STEP_DESCRIPTIONS.keys()), justify='center'))
    print()
    print('caution: for each supported language, only a certain subset of syntax'
          ' and functionality is supported')


def parse_args(args=None):
    """Parse commandline arguments of transpyle CLI."""

    parser = argparse.ArgumentParser(
        prog=PROG_NAME,
        description='Human-oriented and HPC-oriented transpiler.',
        epilog=COPYRIGHT_NOTICE, formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    parser.add_argument('source', nargs=('?' if len(sys.argv) > 1 else None), help='source path')
    parser.add_argument('target', nargs='?',
                        help='target path, print results to stdout if not provided')
    parser.add_argument('--help-languages', '--help-langs', '--languages', '--langs',
                        action='store_true',
                        help='display list of suported languages as well as scope of their support'
                        ' and exit')
    parser.add_argument('--from-language', '--from', type=str, default=None,
                        help='programming language to transpile from, detected if not provided')
    parser.add_argument('--to-language', '--to', type=str, default=None,
                        help='programming language to transpile to, detected from target path')
    parser.add_argument('--scopes', '--scope', metavar='slice', type=slice, nargs='*', default=None,
                        help='only given line scopes are transpiled')
    parser.add_argument('--objects', '--object', '--obj', metavar='pattern', type=str, nargs='*',
                        default=None,
                        help='transpile only selected object(s) within the file (accepts regular'
                        ' expressions), whole file is transpiled if not provided')
    parser.add_argument('--keep', action='store_true',
                        help='do not discard not-transpiled scopes of the code')
    parser.add_argument('--transformations', metavar='name', type=str, nargs='*',
                        help='specify Python script that defines performed AST transformations')

    parsed_args = parser.parse_args(args)

    return parsed_args


def main(args=None):
    """Parse commandline arguments and execute transpyle accordingly."""

    parsed_args = parse_args(args)

    if parsed_args.help_languages:
        print('transpilation step support for each supported language')
        print()
        for step, desc in STEP_DESCRIPTIONS.items():
            print('{}:'.format(step))
            print('  {}'.format(desc))
        print()
        show_supported_langs()
        print()
        print('{}, {}'.format(PROG_NAME, COPYRIGHT_NOTICE))
        return

    if parsed_args.source is None:
        raise NotImplementedError('source path was not provided')

    if parsed_args.target is None:
        raise NotImplementedError('printing to stdout not supported yet')

    if any(_ is None for _ in (parsed_args.from_language, parsed_args.to_language)):
        raise NotImplementedError('language detection not supported yet')

    if parsed_args.objects is not None:
        raise NotImplementedError('object selection not supported yet')

    if parsed_args.scopes is not None:
        raise NotImplementedError('code scope selection not supported yet')

    if parsed_args.keep:
        raise NotImplementedError('--keep option not suppored yet')

    if parsed_args.transformations is not None:
        raise NotImplementedError('--trasformations option not suppored yet')

    from_language = Language.find(parsed_args.from_language)
    to_language = Language.find(parsed_args.to_language)

    reader = CodeReader(from_language.file_extensions)
    translator = AutoTranslator(from_language, to_language)
    writer = CodeWriter(to_language.default_file_extension)

    from_path = pathlib.Path(parsed_args.source)
    to_path = pathlib.Path(parsed_args.target)

    from_code = reader.read_file(from_path)
    to_code = translator.translate(from_code, from_path)
    writer.write_file(to_code, to_path)
