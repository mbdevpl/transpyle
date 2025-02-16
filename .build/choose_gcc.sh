#!/usr/bin/env bash
# set -Eeuxo pipefail

# if [[ "$(uname)" == "Linux" ]]; then
#   sudo update-alternatives \
#     --install /usr/local/bin/gcc gcc /usr/bin/gcc-7 70 \
#     --slave /usr/local/bin/g++ g++ /usr/bin/g++-7 \
#     --slave /usr/local/bin/cpp gcc-cpp /usr/bin/cpp-7 \
#     --slave /usr/local/bin/gfortran gfortran /usr/bin/gfortran-7 \
#     --slave /usr/local/bin/gcc-ar gcc-ar /usr/bin/gcc-ar-7 \
#     --slave /usr/local/bin/gcc-nm gcc-nm /usr/bin/gcc-nm-7 \
#     --slave /usr/local/bin/gcc-ranlib gcc-ranlib /usr/bin/gcc-ranlib-7 \
#     --slave /usr/local/bin/gcov gcov /usr/bin/gcov-7 \
#     --slave /usr/local/bin/gcov-dump gcov-dump /usr/bin/gcov-dump-7
#   sudo update-alternatives --install /usr/bin/cc cc /usr/local/bin/gcc 100
#   sudo update-alternatives --install /usr/bin/c++ c++ /usr/local/bin/g++ 100
#   sudo update-alternatives --install /lib/cpp cpp /usr/local/bin/cpp 100
#   sudo update-alternatives --install /usr/bin/f77 f77 /usr/local/bin/gfortran 100
#   sudo update-alternatives --install /usr/bin/f95 f95 /usr/local/bin/gfortran 100
# fi

if [[ "$(uname)" == "Darwin" ]]; then
  BIN_ROOT_DIR="/usr/local/bin"
  which gcc-$1
  which gcc
  sudo ln -s $(which gcc-$1) "${BIN_ROOT_DIR}/gcc"
  which gcc
  sudo ln -s $(which g++-$1) "${BIN_ROOT_DIR}/g++"
  sudo ln -s $(which cpp-$1) "${BIN_ROOT_DIR}/cpp"
  # sudo ln -s /usr/local/bin/gfortran-$1 /usr/local/bin/gfortran  # already exists
  sudo ln -s $(which gcc-ar-$1) "${BIN_ROOT_DIR}/gcc-ar"
  sudo ln -s $(which gcc-nm-$1) "${BIN_ROOT_DIR}/gcc-nm"
  sudo ln -s $(which gcc-ranlib-$1) "${BIN_ROOT_DIR}/gcc-ranlib"
  sudo ln -s $(which gcov-$1) "${BIN_ROOT_DIR}/gcov"
  sudo ln -s $(which gcov-dump-$1) "${BIN_ROOT_DIR}/gcov-dump"
fi
