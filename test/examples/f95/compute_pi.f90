
function compute_pi(segments)
  implicit none

  integer, intent(in) :: segments
  real*8 :: compute_pi

  real*8 :: polygon_edge_length_squared
  integer :: polygon_sides
  integer :: i

  polygon_edge_length_squared = 2.0
  polygon_sides = 2
  do i = 1, segments
    polygon_edge_length_squared = -sqrt(1 - polygon_edge_length_squared / 4) * 2 + 2
    polygon_sides = polygon_sides * 2
  end do
  compute_pi = sqrt(polygon_edge_length_squared) * polygon_sides
  return
end function
