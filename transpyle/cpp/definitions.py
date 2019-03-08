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
    '__float128': 'np.float128',
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

CPP_PYTHON_CLASS_PAIRS = {
    'std::__cxa_refcounted_exception': 'Exception',
    # STL containers
    'std::array': 'st.ndarray',
    'std::valarray': 'st.ndarray',
    'std::vector': 't.List',
    'std::forward_list': 't.List',
    'std::list': 't.List',
    'std::unordered_set': 't.Set',
    'std::set': 't.Set',
    'std::unordered_map': 't.Dict',
    'std::map': 't.Dict'}

CPP_STL_CLASSES = {
    'std::array', 'std::valarray',
    'std::vector', 'std::forward_list', 'std::list',
    'std::unordered_set', 'std::set',
    'std::unordered_map', 'std::map'}
