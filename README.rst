.. role:: bash(code)
    :language: bash

.. role:: python(code)
    :language: python


transpyle
=========

.. image:: https://img.shields.io/pypi/v/transpyle.svg
    :target: https://pypi.python.org/pypi/transpyle
    :alt: package version from PyPI

.. image:: https://travis-ci.org/mbdevpl/transpyle.svg?branch=master
    :target: https://travis-ci.org/mbdevpl/transpyle
    :alt: build status from Travis CI

.. image:: https://codecov.io/gh/mbdevpl/transpyle/branch/master/graph/badge.svg
    :target: https://codecov.io/gh/mbdevpl/transpyle
    :alt: test coverage from Codecov

.. image:: https://img.shields.io/pypi/l/transpyle.svg
    :target: https://github.com/mbdevpl/transpyle/blob/master/NOTICE
    :alt: license

Human-oriented and high-performing transpiler for Python.

The main aim of transpyle is to let everyone who can code well enough in Python,
benefit from modern high-performing computer hardware without need to reimplement their application
in one of traditional efficient languages such as C or Fortran.


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

Transpyle intends to support selected subsets of: C, C++, Cython, Fortran, OpenCL and Python.

For each language pair and direction of translation, the set of supported features may differ.


C to Python AST
~~~~~~~~~~~~~~~

C-specific AST is created via pycparse, and some of elementary C syntax is transformed into
Python AST.


Python AST to C
~~~~~~~~~~~~~~~

Not implemented yet.


C++ to Python AST
~~~~~~~~~~~~~~~~~

Parsing declarations, but not definitions (i.e. function signature, not body). And only selected
subset of basic types and basic syntax is supported.


Python AST to C++
~~~~~~~~~~~~~~~~~

Not implemented yet.


Cython to Python AST
~~~~~~~~~~~~~~~~~~~~

Not implemented yet.


Python AST to Cython
~~~~~~~~~~~~~~~~~~~~

Not implemented yet.


Fortran to Python AST
~~~~~~~~~~~~~~~~~~~~~

Fortran-specific AST is created via Open Fortran Parser, then that AST is translated
into Python AST.


Python AST to Fortran
~~~~~~~~~~~~~~~~~~~~~

Currently, the Fortran unparser uses special attribute :python:`fortran_metadata` attached
to selected Python AST nodes, and therefore unparsing raw Python AST created directly from ordinary
Python file might not work as expected.

The above behaviour will change in the future.

OpenCL to Python AST
~~~~~~~~~~~~~~~~~~~~

Not implemented yet.


Python AST to OpenCL
~~~~~~~~~~~~~~~~~~~~

Not implemented yet.


Python to Python AST
~~~~~~~~~~~~~~~~~~~~

Python 3.6 with whole-line comments outside expressions is fully supported.
Presence of end-of-line comments or comments in expressions might result in errors.


Python AST to Python
~~~~~~~~~~~~~~~~~~~~

Python 3.6 with whole-line comments outside expressions is fully supported.
Presence of end-of-line comments or comments in expressions might result in errors.


requirements
------------

Python >= 3.5.

Python libraries as specified in `<requirements.txt>`_.

Building and running tests additionally requires packages listed in `<dev_requirements.txt>`_.

Support for transpilation from/to specific language requires additional Python packages
specified in `<extras_requirements.json>`_, which can be installed using the pip extras
installation formula :bash:`pip3 install transpyle[extras]` where those :bash:`extras`
can be one or more of the following:

*   All supported languages: :bash:`all`

*   C: :bash:`c`

*   C++: :bash:`cpp`

*   Cython: :bash:`cython`

*   Fortran: :bash:`fortran`

*   OpenCL: :bash:`opencl`

Therefore to enable support for all languages, execute :bash:`pip3 install transpyle[all]`.
Alternatively, to enable support for C++ and Fortran only, execute
:bash:`pip3 install transpyle[cpp,fortran]`.

Additionally, support for some languages requires the following software to be installed:

*   C, C++: SWIG (Simplified Wrapper and Interface Generator) with executable `swig`

*   Fortran: a modern Fortran compiler with executable `gfortran`


docker image
------------

There is a docker image prepared so that you can easily try the transpiler.

First, download and run the docker container (migth require sudo):

.. code:: bash

    docker pull "mbdevpl/transpyle"
    docker run -h transmachine -it "mbdevpl/transpyle"

Then, in the container:

.. code:: bash

    python3 -m jupyter notebok --ip="$(hostname -i)" --port=8080

Open the shown link in your host's web browser, navigate to `examples.ipynb`_,
and start transpiling!
