"""Unparsing of general AST into code in given language."""

import logging
# import typing as t

import horast

from .registry import Registry
from .language import Language

_LOG = logging.getLogger(__name__)


def unparsing_unsupported(language_name: str, syntax, comment: str = None, error: bool = True):
    unparsed = 'invalid'
    try:
        unparsed = '"""{}"""'.format(horast.unparse(syntax).strip())
    except AttributeError:
        pass
    if comment is not None:
        comment = ' ' + comment
    _LOG.error('unparsing %s%s like """%s""" (%s in Python) is unsupported for %s',
               syntax.__class__.__name__, comment, horast.dump(syntax), unparsed, language_name)
    if error:
        raise SyntaxError(
            'unparsing {}{} like """{}""" ({} in Python) is unsupported for {}'.format(
                syntax.__class__.__name__, comment, horast.dump(syntax), unparsed, language_name))


class Unparser(Registry):

    """Output code in a given language."""

    def __init__(self, language: Language):
        self.language = language

    def unparse(self, tree) -> str:
        raise NotImplementedError()
