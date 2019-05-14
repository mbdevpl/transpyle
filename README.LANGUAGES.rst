.. role:: bash(code)
    :language: bash

.. role:: cpp(code)
    :language: cpp

.. role:: fortran(code)
    :language: fortran

.. role:: python(code)
    :language: python


=============================
Language support in transpyle
=============================

.. contents::
    :backlinks: none


C
===

To be written.


C++
===

Recognized elementary variable types:

.. code:: cpp

    bool x;
    int x;
    float x;
    char x;


Recognized container variable types:

.. code:: cpp

    vector<T> x;


Fortran
=======

Supported elementary variable types:

.. code:: fortran

    logical :: x
    integer :: x
    real :: x
    character :: x

Supported array variable types:

.. code:: fortran

    T, dimensions(10, 10) :: x
    T, dimensions(:, :) :: x
    T, dimensions(*) :: x

Recognized variable type modifiers:

.. code:: fortran

    allocatable
    intent(in)
    intent(out)
    parameter

Recognized intrinsic functions:

.. code:: fortran

    log
    log10


Python
======

All language constructs are recognized.
