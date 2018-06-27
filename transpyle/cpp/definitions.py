"""Definitions for C++."""

CPP_PYTHON_TYPE_PAIRS = {
    # boolean
    'bool': 'bool',
    # integers
    'short int': 'np.int',  # incorrect
    'int': 'int',
    'long int': 'np.int',  # incorrect
    'long long int': 'np.int',  # incorrect
    'short unsigned int': 'np.uint',  # incorrect
    'unsigned int': 'np.uint',
    'long unsigned int': 'np.uint',  # incorrect
    'long long unsigned int': 'np.uint',  # incorrect
    '__int128': 'np.int128',
    'unsigned __int128': 'np.uint128',
    # floating point
    'float': 'float',
    'double': 'np.double',
    'long double': 'np.double',  # incorrect
    # characters and strings
    'char': 'str',  # incorrect
    'signed char': 'str',  # incorrect
    'unsigned char': 'str',  # incorrect
    'char16_t': 'str',  # incorrect
    'char32_t': 'str',  # incorrect
    'wchar_t': 'str',  # incorrect
    # pointers
    # other
    'void': 'None'}
