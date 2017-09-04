
from .registry import Registry

class Compiler(Registry):

    def __init__(self, language, *args, **kwargs):
        raise NotImplementedError()

    def compile(self, code: str, *args, **kwargs):
        raise NotImplementedError()
