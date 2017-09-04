
import inspect

from ..general import Language

_PYTHON = Language(['Python', 'Py'], ['.py'])

Language.register(_PYTHON, ['Python', 'Py'])


def transpile(function, to_language, *args, **kwargs):
    """Meant to be used as decorator."""

    #translator = Translator('Python 3.6', to_language, *args, **kwargs)
    from_code = inspect.getsource(function)
    #python_ast = 
    to_code = translator.translate(from_code)

    compiler = Compiler(to_language, *args, **kwargs)
    compiled = compiler.compile(to_code)

    binder = Binder(to_language)
    binding = binder.bind(compiled)

    return binding
