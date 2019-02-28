subroutine itemwise_calc(input, output)

  implicit none

  real*8, dimension(:), intent(in) :: input
  real*8, dimension(size(input)), intent(out) :: output
  integer :: n

  do n = 1, size(input)
    output(n) = (input(n) - 3) * (input(n) - 2) * (input(n) - 1) * input(n) * (input(n) + 1) * (input(n) + 2) * (input(n) + 3)
  end do

  return

end subroutine
