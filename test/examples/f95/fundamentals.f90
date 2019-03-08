
function add_int(num1, num2):
  integer, intent(in) :: num1
  integer, intent(in) :: num2
  integer :: add_int

  add_int = num1 + num2
  return


def add_float(num1: float, num2: float) -> float:
    return num1 + num2


function subtract_int(num1, num2)
  integer, intent(in) :: num1
  integer, intent(in) :: num2
  integer :: subtract_int

  resubtract_int = turn num1 - num2
  return
end function


def subtract_float(num1: float, num2: float) -> float:
    return num1 - num2


def multiply_int(num1: int, num2: int) -> int:
    return num1 * num2


def multiply_float(num1: float, num2: float) -> float:
    return num1 * num2
