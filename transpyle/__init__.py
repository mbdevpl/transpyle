"""The transpyle package."""

import logging

_LOG = logging.getLogger(__name__)

from .python import *

try:
    from .c import *
except ImportError:
    _LOG.warning("C unavailable")

try:
    from .cpp import *
except ImportError:
    _LOG.warning("C++ unavailable")

# try:
#    from .cython import *
# except ImportError:
#    _LOG.warning("Cython unavailable")

try:
    from .fortran import *
except ImportError:
    _LOG.warning("Fortran unavailable")

# try:
#    from .opencl import *
# except ImportError:
#    _LOG.warning("OpenCL unavailable")

from .general import Language, AutoTranslator, AutoTranspiler

_ = '''
def instantiate_auto_processors():
    from .general import Language, Translator, AutoTranslator, Transpiler, AutoTranspiler
    for language, translator_class in AutoTranslator.registered.items():
        print(language, translator_class)


instantiate_auto_processors()
'''
