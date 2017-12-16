"""Commandline utility for transpyle package."""

import argparse
import pathlib

from .general import Language, CodeReader, CodeWriter, Translator


def main(args=None, namespace=None):
    """Parse commandline arguments and execute transpyle accordingly."""

    parser = argparse.ArgumentParser()
    parser.add_argument('source', help='source path')
    parser.add_argument('target', help='target path')
    parser.add_argument('--from-language', '--from', type=str, default=None,
                        help='programming language to transpile from, detected if not provided')
    parser.add_argument('--to-language', '--to', type=str, default=None,
                        help='programming language to transpile to, detected from target path')
    parser.add_argument('--objects', '--object', '--obj', type=str, default=None,
                        help='transpile only selected object(s) within the file (acceps regular'
                        ' expressions), whole file is transpiled if not provided')

    args = parser.parse_args(args, namespace)

    if any(_ is None for _ in (args.from_language, args.to_language)):
        raise NotImplementedError('language detection not supported yet')

    if args.objects is not None:
        raise NotImplementedError('object selection not supported yet')

    from_language = Language.find(args.from_language)
    to_language = Language.find(args.to_language)

    reader = CodeReader(from_language.file_extensions)
    translator = Translator(from_language, to_language)
    writer = CodeWriter(to_language.default_file_extension)

    from_path = pathlib.Path(args.source)
    to_path = pathlib.Path(args.target)

    from_code = reader.read_file(from_path)
    to_code = translator.translate(from_code, from_path)
    writer.write_file(to_code, to_path)
