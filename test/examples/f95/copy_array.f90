subroutine copy_array(input, output)

  implicit none

  real*8, dimension(:), intent(in) :: input
  real*8, dimension(size(input)), intent(out) :: output
  !, allocatable
  integer :: n

  !allocate(output(size(input)))

  do n = 1, size(input)
    output(n) = input(n)
  end do

  return

end subroutine
