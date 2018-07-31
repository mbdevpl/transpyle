
#include <cmath>

double compute_pi(int segments) {
  double polygon_edge_length_squared = double(2.0);
  int polygon_sides = 2;
  for(int _ = 0; _ < segments; ++_) {
    polygon_edge_length_squared = -sqrt(1 - polygon_edge_length_squared / 4) * 2 + 2;
    polygon_sides *= 2;
  }
  return sqrt(polygon_edge_length_squared) * polygon_sides;
}
