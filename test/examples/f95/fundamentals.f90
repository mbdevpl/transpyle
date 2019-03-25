
function add_integer(num1, num2)
  implicit none
  integer, intent(in) :: num1
  integer, intent(in) :: num2
  integer :: add_integer

  add_integer = num1 + num2
  return
end function

function add_real(num1, num2)
  implicit none
  real, intent(in) :: num1
  real, intent(in) :: num2
  real :: add_real

  add_real = num1 + num2
  return
end function

function subtract_integer(num1, num2)
  implicit none
  integer, intent(in) :: num1
  integer, intent(in) :: num2
  integer :: subtract_integer

  subtract_integer = num1 - num2
  return
end function

function subtract_real(num1, num2)
  implicit none
  real, intent(in) :: num1
  real, intent(in) :: num2
  real :: subtract_real

  subtract_real = num1 - num2
  return
end function

function multiply_integer(num1, num2)
  implicit none
  integer, intent(in) :: num1
  integer, intent(in) :: num2
  integer :: multiply_integer

  multiply_integer = num1 * num2
  return
end function

function multiply_real(num1, num2)
  implicit none
  real, intent(in) :: num1
  real, intent(in) :: num2
  real :: multiply_real

  multiply_real = num1 * num2
  return
end function

function is_positive_int(num)
  implicit none
  integer, intent(in) :: num
  logical :: is_positive_int

  is_positive_int = num > 0
  return
end function

function is_zero_int(num)
  implicit none
  integer, intent(in) :: num
  logical :: is_zero_int

  is_zero_int = num == 0
  return
end function

function is_negative_int(num)
  implicit none
  integer, intent(in) :: num
  logical :: is_negative_int

  is_negative_int = num < 0
  return
end function

function is_single_digit_int(num)
  implicit none
  integer, intent(in) :: num
  logical :: is_single_digit_int

  is_single_digit_int = num > -10 .and. num < 10
  return
end function

function is_not_single_digit_int(num)
  implicit none
  integer, intent(in) :: num
  logical :: is_not_single_digit_int

  is_not_single_digit_int = num <= -10 .or. num >= 10
  return
end function
