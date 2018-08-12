"""Collection of definitions for Fortran language support."""

import typing as t

import typed_ast.ast3 as typed_ast3

from ..pair import make_slice_from_call

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

PYTHON_FORTRAN_TYPE_PAIRS = {value: key for key, value in FORTRAN_PYTHON_TYPE_PAIRS.items()}

PYTHON_TYPE_ALIASES = {
    'bool': ('np.bool_',),
    'int': ('np.int_', 'np.intc', 'np.intp'),
    'np.float32': ('np.single',),
    'np.float64': ('np.double', 'np.float_',)}

for _name, _aliases in PYTHON_TYPE_ALIASES.items():
    for _alias in _aliases:
        PYTHON_FORTRAN_TYPE_PAIRS[_alias] = PYTHON_FORTRAN_TYPE_PAIRS[_name]

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
    'acos': ('numpy', 'arccos'),
    'aimag': None,
    'aint': None,
    'anint': None,
    'asin': ('numpy', 'arcsin'),
    'atan': ('numpy', 'arctan'),
    'atan2': None,
    'char': None,
    'cmplx': None,
    'conjg': ('numpy', 'conj'),
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
    'sign': ('numpy', 'sign'),
    'sin': ('numpy', 'sin'),
    'sinh': ('numpy', 'sinh'),
    'sqrt': ('numpy', 'sqrt'),
    'tan': ('numpy', 'tan'),
    'tanh': ('numpy', 'tanh'),
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
    'epsilon': ('numpy', 'finfo', 'eps'),
    'huge': ('numpy', 'finfo', 'max'),
    'maxexponent': None,
    'minexponent': None,
    'precision': None,
    'radix': None,
    'range': None,
    'tiny': ('numpy', 'finfo', 'tiny'),  # np.finfo(np.double).tiny ,
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
    'present': 'is_not_none',  # TODO: TMP
    'set_exponent': None,
    # Fortran 2003
    # Fortran 2008
    }


def _transform_print_call(call):
    if not hasattr(call, 'fortran_metadata'):
        call.fortran_metadata = {}
    call.fortran_metadata['is_transformed'] = True
    if len(call.args) == 1:
        arg = call.args[0]
        if isinstance(arg, typed_ast3.Call) and isinstance(arg.func, typed_ast3.Attribute):
            label = int(arg.func.value.id.replace('format_label_', ''))
            call.args = [typed_ast3.Num(n=label)] + arg.args
            return call
    call.args.insert(0, typed_ast3.Ellipsis())
    return call


PYTHON_FORTRAN_INTRINSICS = {
    'np.arcsin': 'asin',
    'np.arctan': 'atan',
    'np.argmin': 'minloc',
    'np.argmax': 'maxloc',
    'np.array': lambda _: _.args[0],
    'np.conj': 'conjg',
    'np.cos': 'cos',
    'np.dot': 'dot_product',
    'np.finfo.eps': 'epsilon',
    'np.finfo.max': 'huge',
    'np.finfo.tiny': 'tiny',
    'np.maximum': 'max',
    'np.minimum': 'min',
    'np.sign': 'sign',
    'np.sin': 'sin',
    'np.sinh': 'sinh',
    'np.sqrt': 'sqrt',
    'np.zeros': lambda _: typed_ast3.Num(n=0),
    'print': _transform_print_call,
    'os.environ': 'getenv',
    'is_not_none': 'present',
    'MPI.Init': 'MPI_Init',
    'MPI.COMM_WORLD.Comm_size': 'MPI_Comm_size',
    'MPI.COMM_WORLD.Comm_rank': 'MPI_Comm_rank',
    'MPI.COMM_WORLD.Barrier': 'MPI_Barrier',
    'MPI.Bcast': 'MPI_Bcast',
    'MPI.Allreduce': 'MPI_Allreduce',
    'MPI.Finalize': 'MPI_Finalize',
    '{expression}.sum': None,
    'Fortran.file_handles[{name}].read': None,
    'Fortran.file_handles[{name}].close': None,
    '{name}.rstrip': None,
    'slice': make_slice_from_call
    }

INTRINSICS_SPECIAL_CASES = {'getenv', 'trim', 'count'}

PYTHON_TO_FORTRAN_SPECIAL_CASES = {'print', ('numpy', 'array'), ('numpy', 'zeros')}

INTRINSICS_PYTHON_TO_FORTRAN = {value: key for key, value in INTRINSICS_FORTRAN_TO_PYTHON.items()
                                if value is not None}

CALLS_SPECIAL_CASES = {(..., 'rstrip'), ('os', 'environ'), (..., 'count')}
