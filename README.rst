.. role:: python(code)
    :language: python


transpyle
=========

.. image:: https://img.shields.io/pypi/v/transpyle.svg
    :target: https://pypi.python.org/pypi/transpyle
    :alt: package version from PyPI

.. image:: https://img.shields.io/pypi/l/transpyle.svg
    :target: https://github.com/mbdevpl/transpyle/blob/master/NOTICE
    :alt: license

Human-oriented and high-performing transpiler for Python.

The main aim of transpyle is to let everyone who can code well enough in Python,
benefit from modern high-performing computer hardware.


framework design
----------------

Framework consists of mainly the following kinds of modules:

*   parser

*   abstract syntax tree (AST) generalizer

*   unparser

*   compiler

*   binder

At least some of the modules are expected to be implemented for each language
supported by the framework.

The modules are responsible for transforming the data between the following states:

*   language-specific code

*   language-specific AST

*   extended Python AST

*   compiled binary

*   Python interface for compiled binary

And thus:

*   parser transforms language-specific code into language-specific AST

*   AST generalizer transforms language-specific AST into extended Python AST

*   unparser transforms extended Python AST into language-specific code

*   compiler transforms language-specific code into compiled binary

*   binder transforms compiled binary into Python interface for compiled binary

The intermediate meeting point which effectively allows code to actually be transpiled between
languages, is the extended Python AST.


language support
----------------

Transpyle intends to support selected subsets of: C++, Fortran, OpenCL, Python.

For each language pair and direction of translation, the set of supported features may differ.


C++ to Python AST
~~~~~~~~~~~~~~~~~

TODO.


Python AST to C++
~~~~~~~~~~~~~~~~~

TODO.


Fortran to Python AST
~~~~~~~~~~~~~~~~~~~~~

TODO.

Dependencies:

*   Open Fortran Parser

*   Open Fortran Parser XML

*   open_fortran_parser (Python package)


Python AST to Fortran
~~~~~~~~~~~~~~~~~~~~~

TODO.

Dependencies:

*   f2py


OpenCL to Python AST
~~~~~~~~~~~~~~~~~~~~

TODO.


Python AST to OpenCL
~~~~~~~~~~~~~~~~~~~~

TODO.


Python to Python AST
~~~~~~~~~~~~~~~~~~~~

Python 3.6 with whole-line comments outside expressions is fully supported.
Presence of end-of-line comments or comments in expressions might result in errors.

Dependencies:

*   inspect

*   typed_ast

*   horast


Python AST to Python
~~~~~~~~~~~~~~~~~~~~

Python 3.6 with whole-line comments outside expressions is fully supported.
Presence of end-of-line comments or comments in expressions might result in errors.

Dependencies:

*   typed_astunparse

*   horast


requirements
------------

Python >= 3.5.

Python libraries as specified in `<requirements.txt>`_.

Building and running tests additionally requires packages listed in `<dev_requirements.txt>`_.
