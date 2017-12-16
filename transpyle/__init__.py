"""The transpyle package."""

import logging

_LOG = logging.getLogger()

try:
    from .c import *
except ImportError:
    _LOG.warning("C unavailable")

try:
    from .cpp import *
except ImportError:
    _LOG.warning("C++ unavailable")

try:
    from .cython import *
except ImportError:
    _LOG.warning("Cython unavailable")

try:
    from .fortran import *
except ImportError:
    _LOG.warning("Fortran unavailable")

try:
    from .opencl import *
except ImportError:
    _LOG.warning("OpenCL unavailable")

from .python import *
