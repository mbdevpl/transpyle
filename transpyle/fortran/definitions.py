"""Collection of definitions for Fortran language support."""

import typing as t

import typed_ast.ast3 as typed_ast3

FORTRAN_PYTHON_TYPE_PAIRS = {
    ('logical', None): 'bool',
    ('integer', None): 'int',
    ('real', None): 'float',
    ('character', t.Any): 'str',
    ('integer', 1): 'np.int8',
    ('integer', 2): 'np.int16',
    ('integer', 4): 'np.int32',
    ('integer', 8): 'np.int64',
    ('real', 2): 'np.float16',
    ('real', 4): 'np.float32',
    ('real', 8): 'np.float64'}

FORTRAN_PYTHON_OPERATORS = {
    # binary
    '+': (typed_ast3.BinOp, typed_ast3.Add),
    '-': (typed_ast3.BinOp, typed_ast3.Sub),
    '*': (typed_ast3.BinOp, typed_ast3.Mult),
    # missing: MatMult
    '/': (typed_ast3.BinOp, typed_ast3.Div),
    '%': (typed_ast3.BinOp, typed_ast3.Mod),
    '**': (typed_ast3.BinOp, typed_ast3.Pow),
    '//': (typed_ast3.BinOp, typed_ast3.Add),  # concatenation operator, only in Fortran
    # LShift
    # RShift
    # BitOr
    # BitXor
    # BitAnd
    # missing: FloorDiv
    '.eq.': (typed_ast3.Compare, typed_ast3.Eq),
    '==': (typed_ast3.Compare, typed_ast3.Eq),
    '.ne.': (typed_ast3.Compare, typed_ast3.NotEq),
    '/=': (typed_ast3.Compare, typed_ast3.NotEq),
    '.lt.': (typed_ast3.Compare, typed_ast3.Lt),
    '<': (typed_ast3.Compare, typed_ast3.Lt),
    '.le.': (typed_ast3.Compare, typed_ast3.LtE),
    '<=': (typed_ast3.Compare, typed_ast3.LtE),
    '.gt.': (typed_ast3.Compare, typed_ast3.Gt),
    '>': (typed_ast3.Compare, typed_ast3.Gt),
    '.ge.': (typed_ast3.Compare, typed_ast3.GtE),
    '>=': (typed_ast3.Compare, typed_ast3.GtE),
    # Is
    # IsNot
    # In
    # NotIn
    '.and.': (typed_ast3.BoolOp, typed_ast3.And),
    '.or.': (typed_ast3.BoolOp, typed_ast3.Or),
    # unary
    # '+': (typed_ast3.UnaryOp, typed_ast3.UAdd),
    # '-': (typed_ast3.UnaryOp, typed_ast3.USub),
    '.not.': (typed_ast3.UnaryOp, typed_ast3.Not),
    # Invert: (typed_ast3.UnaryOp, typed_ast3.Invert)
    }

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
