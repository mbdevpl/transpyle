"""Commandline utility for transpyle package."""

import argparse
import pathlib
import sys

import ordered_set
import pandas as pd

from .general import Language, CodeReader, CodeWriter, AutoTranslator
from .general import Parser, AstGeneralizer, Unparser, Compiler, Binder


def query_registry() -> pd.DataFrame:
    """Gather information about supported languages in transpyle and scope of their support."""
    classes = (Parser, AstGeneralizer, Unparser, Compiler, Binder)
    distinct_languages = list(ordered_set.OrderedSet(Language.registered.values()))
    language_support = {}
    for language in distinct_languages:
        language_support[language] = [cls.find(language) is not None for cls in classes]
    return pd.DataFrame(columns=classes, index=distinct_languages,
                        data=[support for _, support in language_support.items()], dtype=bool)


def main(args=None, namespace=None):
    """Parse commandline arguments and execute transpyle accordingly."""

    prog_name = 'transpyle'
    copyright_notice = 'Copyright 2017 Mateusz Bysiek https://mbdevpl.github.io/,' \
        ' Apache License 2.0'

    parser = argparse.ArgumentParser(
        prog=prog_name,
        description='Human-oriented and HPC-oriented transpiler.',
        epilog=copyright_notice)
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
    parser.add_argument('--objects', '--object', '--obj', type=str, default=None,
                        help='transpile only selected object(s) within the file (acceps regular'
                        ' expressions), whole file is transpiled if not provided')

    args = parser.parse_args(args, namespace)

    if args.help_languages:
        support_data = query_registry()
        step_descriptions = {
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
        support_data = pd.DataFrame(
            columns=[cls.__name__ for cls in support_data.columns],
            index=[language.default_name for language in support_data.index],
            data=[['✓' if support else '' for support in data_row]
                  for _, data_row in support_data.iterrows()], dtype=str)
        print('transpilation step support for each supported language')
        print()
        for step, desc in step_descriptions.items():
            print('{}:'.format(step))
            print('  {}'.format(desc))
        print()
        print(support_data.to_string(header=list(step_descriptions.keys()), justify='center'))
        print()
        print('caution: for each supported language, only a certain subset of syntax'
              ' and functionality is supported')
        print()
        print('{}, {}'.format(prog_name, copyright_notice))
        return

    if args.source is None:
        raise NotImplementedError('source path was not provided')

    if args.target is None:
        raise NotImplementedError('printing to stdout not supported yet')

    if any(_ is None for _ in (args.from_language, args.to_language)):
        raise NotImplementedError('language detection not supported yet')

    if args.objects is not None:
        raise NotImplementedError('object selection not supported yet')

    from_language = Language.find(args.from_language)
    to_language = Language.find(args.to_language)

    reader = CodeReader(from_language.file_extensions)
    translator = AutoTranslator(from_language, to_language)
    writer = CodeWriter(to_language.default_file_extension)

    from_path = pathlib.Path(args.source)
    to_path = pathlib.Path(args.target)

    from_code = reader.read_file(from_path)
    to_code = translator.translate(from_code, from_path)
    writer.write_file(to_code, to_path)
