
#include <vector>

std::vector<double> copy_array(std::vector<double> input_data) {

  std::vector<double> output_data;

  for(int i = 0; i < input_data.size(); ++i) {
    output_data[i] = input_data[i];
  }

  return output_data;
}
