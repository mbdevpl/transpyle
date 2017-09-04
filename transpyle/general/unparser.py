""""""

import logging
import typing as t

from .registry import Registry
from .language import Language


class Unparser(Registry):

    def __init__(self, language: Language):
        self.language = language
