
def add_int(num1: int, num2: int) -> int:
    return num1 + num2


def add_float(num1: float, num2: float) -> float:
    return num1 + num2


def subtract_int(num1: int, num2: int) -> int:
    return num1 - num2


def subtract_float(num1: float, num2: float) -> float:
    return num1 - num2


def multiply_int(num1: int, num2: int) -> int:
    return num1 * num2


def multiply_float(num1: float, num2: float) -> float:
    return num1 * num2


def is_positive_int(num: int) -> bool:
    return num > 0


def is_zero_int(num: int) -> bool:
    return num == 0


def is_negative_int(num: int) -> bool:
    return num < 0


def is_single_digit_int(num: int) -> bool:
    return num > -10 and num < 10


def is_not_single_digit_int(num: int) -> bool:
    return num <= -10 or num >= 10
