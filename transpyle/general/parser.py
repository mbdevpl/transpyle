
from .registry import Registry
from .language import Language

class Parser(Registry):

    def __init__(self, language: Language):
        self.language = language
