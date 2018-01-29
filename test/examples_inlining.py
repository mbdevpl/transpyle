"""Test examples for AST inlining."""


def buy_products(spam=0, ham=0, eggs=0):
    buy(spam)
    buy(ham)
    buy(eggs)


def buy(product: int = -1):
    print('bought '.format(product))


def buy_products_inlined(spam=0, ham=0, eggs=0):
    print('bought '.format(spam))
    print('bought '.format(ham))
    print('bought '.format(eggs))


def just_return(x=None):
    return return_me(x)


def return_me(a=None):
    return a


def just_return_inlined(x=None):
    return x


def just_assign(x=None, y=None):
    print(x, y)
    x = return_me(y)
    print(x, y)


def just_assign_inlined(x=None, y=None):
    print(x, y)
    x = y
    print(x, y)


def print_and_get_absolute(x=0):
    print(x)
    return absolute_value(x)


def absolute_value(val=0):
    if val > 0:
        return val
    else:
        return -val


def print_and_get_absolute_inlined(x=0):
    print(x)
    if (x > 0):
        return x
    else:
        return (- x)
    return


def inline_oneliner(value1=0, value2=0):
    if add_squares(value1, value2) == 0:
        return 'both values are zero'
    return 'at least one of the values is nonzero'


def add_squares(x=0, y=0):
    return x * x + y * y


def inline_oneliner_inlined(value1=0, value2=0):
    if (((value1 * value1) + (value2 * value2)) == 0):
        return 'both values are zero'
    return 'at least one of the values is nonzero'


# '''def do_work_3d(array):\n    do_work(array, 1)\n    do_work(array, 2)\n''':
# '''def do_work(array, dim):\n    if dim == 1:\n        array[:, 4] = 2\n    if dim == 2:\n'''
