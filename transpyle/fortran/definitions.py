"""Collection of definitions for Fortran language support."""


INTRINSICS_FORTRAN_TO_PYTHON = {
    # Fortran 77
    'abs': 'abs',  # or np.absolute
    'acos': None,
    'aimag': None,
    'aint': None,
    'anint': None,
    'asin': None,
    'atan': None,
    'atan2': None,
    'char': None,
    'cmplx': None,
    'conjg': None,
    'cos': ('numpy', 'cos'),
    'cosh': None,
    'dble': 'float',  # incorrect
    'dim': None,
    'dprod': None,
    'exp': None,
    'ichar': None,
    'index': None,
    'int': 'int',
    'len': None,
    'lge': None,
    'lgt': None,
    'lle': None,
    'llt': None,
    'log': None,
    'log10': None,
    'max': ('numpy', 'maximum'),
    'min': ('numpy', 'minimum'),
    'mod': None,
    'nint': None,
    'real': 'float',
    'sign': None,
    'sin': ('numpy', 'sin'),
    'sinh': None,
    'sqrt': ('numpy', 'sqrt'),
    'tan': None,
    'tanh': None,
    # non-standard Fortran 77
    'getenv': ('os', 'environ'),
    # Fortran 90
    # Character string functions
    'achar': None,
    'adjustl': None,
    'adjustr': None,
    'iachar': None,
    'len_trim': None,
    'repeat': None,
    'scan': None,
    'trim': ('str', 'rstrip'),
    'verify': None,
    # Logical function
    'logical': None,
    # Numerical inquiry functions
    'digits': None,
    'epsilon': None,
    'huge': None,
    'maxexponent': None,
    'minexponent': None,
    'precision': None,
    'radix': None,
    'range': None,
    'tiny': None,
    # Bit inquiry function
    'bit_size': None,
    # Vector- and matrix-multiplication functions
    'dot_product': ('numpy', 'dot'),
    'matmul': None,
    # Array functions
    'all': None,
    'any': None,
    'count': ('ndarray', 'count'),
    'maxval': None,
    'minval': None,
    'product': None,
    'sum': 'sum',
    # Array location functions
    'maxloc': ('numpy', 'argmax'),
    'minloc':  ('numpy', 'argmin'),
    # Fortran 95
    'cpu_time': None,
    'present': None,
    'set_exponent': None,
    # Fortran 2003
    # Fortran 2008
    }

INTRINSICS_SPECIAL_CASES = {'getenv', 'trim', 'count'}

INTRINSICS_PYTHON_TO_FORTRAN = {value: key for key, value in INTRINSICS_FORTRAN_TO_PYTHON.items()
                                if value is not None}

CALLS_SPECIAL_CASES = {(..., 'rstrip'), ('os', 'environ'), (..., 'count')}
