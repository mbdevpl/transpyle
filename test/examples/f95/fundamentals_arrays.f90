
subroutine itemwise_add_integer(input1, input2, output)
  implicit none
  integer, dimension(:), intent(in) :: input1
  integer, dimension(:), intent(in) :: input2
  integer, dimension(size(input1)), intent(out) :: output
  integer :: n

  do n = 1, size(input1)
    output(n) = input1(n) + input2(n)
  end do
  return
end subroutine

subroutine itemwise_add_real(input1, input2, output)
  implicit none
  real, dimension(:), intent(in) :: input1
  real, dimension(:), intent(in) :: input2
  real, dimension(size(input1)), intent(out) :: output
  integer :: n

  do n = 1, size(input1)
    output(n) = input1(n) + input2(n)
  end do
  return
end subroutine

subroutine itemwise_subtract_integer(input1, input2, output)
  implicit none
  integer, dimension(:), intent(in) :: input1
  integer, dimension(:), intent(in) :: input2
  integer, dimension(size(input1)), intent(out) :: output
  integer :: n

  do n = 1, size(input1)
    output(n) = input1(n) - input2(n)
  end do
  return
end subroutine

subroutine itemwise_subtract_real(input1, input2, output)
  implicit none
  real, dimension(:), intent(in) :: input1
  real, dimension(:), intent(in) :: input2
  real, dimension(size(input1)), intent(out) :: output
  integer :: n

  do n = 1, size(input1)
    output(n) = input1(n) - input2(n)
  end do
  return
end subroutine

subroutine itemwise_multiply_integer(input1, input2, output)
  implicit none
  integer, dimension(:), intent(in) :: input1
  integer, dimension(:), intent(in) :: input2
  integer, dimension(size(input1)), intent(out) :: output
  integer :: n

  do n = 1, size(input1)
    output(n) = input1(n) * input2(n)
  end do
  return
end subroutine

subroutine itemwise_multiply_real(input1, input2, output)
  implicit none
  real, dimension(:), intent(in) :: input1
  real, dimension(:), intent(in) :: input2
  real, dimension(size(input1)), intent(out) :: output
  integer :: n

  do n = 1, size(input1)
    output(n) = input1(n) * input2(n)
  end do
  return
end subroutine
