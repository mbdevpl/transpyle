#include <stdbool.h>


int add_int(int num1, int num2) {
  return num1 + num2;
}

float add_float(float num1, float num2) {
  return num1 + num2;
}

int subtract_int(int num1, int num2) {
  return num1 - num2;
}

float subtract_float(float num1, float num2) {
  return num1 - num2;
}

int multiply_int(int num1, int num2) {
  return num1 * num2;
}

float multiply_float(float num1, float num2) {
  return num1 * num2;
}

bool is_positive_int(int num) {
  return num > 0;
}

bool is_zero_int(int num) {
  return num == 0;
}

bool is_negative_int(int num) {
  return num < 0;
}

bool is_single_digit_int(int num) {
  return num > -10 && num < 10;
}

bool is_not_single_digit_int(int num) {
  return num <= -10 || num >= 10;
}
