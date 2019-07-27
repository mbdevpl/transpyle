.. role:: bash(code)
    :language: bash

.. role:: python(code)
    :language: python


=========
transpyle
=========

Human-oriented and high-performing transpiler for Python.

.. image:: https://img.shields.io/pypi/v/transpyle.svg
    :target: https://pypi.org/project/transpyle
    :alt: package version from PyPI

.. image:: https://travis-ci.org/mbdevpl/transpyle.svg?branch=master
    :target: https://travis-ci.org/mbdevpl/transpyle
    :alt: build status from Travis CI

.. image:: https://codecov.io/gh/mbdevpl/transpyle/branch/master/graph/badge.svg
    :target: https://codecov.io/gh/mbdevpl/transpyle
    :alt: test coverage from Codecov

.. image:: https://img.shields.io/github/license/mbdevpl/transpyle.svg
    :target: https://github.com/mbdevpl/transpyle/blob/master/NOTICE
    :alt: license

The main aim of transpyle is to let everyone who can code well enough in Python,
benefit from modern high-performing computer hardware without need to reimplement their application
in one of traditional efficient languages such as C or Fortran.

.. contents::
    :backlinks: none


Framework design
================

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


Features
========

Using Python AST as the intermediate representation, enables the AST to be directly manipulated,
and certain performance-oriented transformations can be applied. Current transpiler implementation
aims at:

*   inlining selected calls
*   decorating selected loops with compiler-extension pragmas

More optimizations will be introduced in the future.

Some (if not all) of the above optimizations may have very limited (if not no) performance impact
in Python, however when C, C++ or Fortran code is generated, the performance gains can be
much greater.


Command-line interface
----------------------

The command-line interface (CLI) of transpyle allows one to translate source code files
in supported languages.



API highlights
--------------

The API of transpyle allows using it to make your Python code faster.

The most notable part of the API is the ``transpile`` decorator, which in it's most basic form
is not very different from Numba's ``jit`` decorator.

.. code:: python

    import transpyle

    @transpyle.transpile('Fortran')
    def my_function(a: int, b: int) -> int:
        return a + b


Additionally, you can use each of the modules of the transpiler individually, therefore transpyle
can support any transformation sequence you are able to express:

.. code:: python

    import pathlib
    import transpyle

    path = pathlib.Path('my_script.py')
    code_reader = transpyle.CodeReader()
    code = code_reader.read_file(path)

    from_language = transpyle.Language.find('Python 3.6')
    to_language = transpyle.Language.find('Fortran 95')
    translator = transpyle.AutoTranslator(from_language, to_language)
    fortran_code = translator.translate(code, path)
    print(fortran_code)


As transpyle is under heavy development, the API might change significantly between versions.


Language support
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

Only very basic syntax is supported currently.


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


Requirements
============

Python 3.5 or later.

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

Additionally, full support for some languages requires the following software to be installed:

*   C++:

    *   a modern C++ compiler -- fully tested with GNU's ``g++`` versions 7 and 8
        and partially tested with LLVM's ``clang++`` version 7

    *   SWIG (Simplified Wrapper and Interface Generator) -- tested with version 3

*   Fortran:

    *   a modern Fortran compiler -- fully tested with GNU's ``gfortran`` versions 7 and 8
        and partially tested with PGI's ``pgfortran`` version 2018

The core functionality of transpyle is platform-independent. However, as support of some languages
depends on presence of additional software, some functionality might be limited/unavailable
on selected platforms.

Transpyle is fully tested on Linux, and partially tested on OS X.


Installation
============

pip
---

.. code:: bash

    pip3 install transpyle[all]


Docker image
------------

There is a docker image prepared so that you can easily try the transpiler.

First, download and run the docker container (migth require sudo):

.. code:: bash

    docker pull "mbdevpl/transpyle"
    docker run -h transmachine -it "mbdevpl/transpyle"


By default, this will download latest more or less stable development build,
if you wish to use a specific release, use :bash:`"mbdevpl/transpyle:version"` instead.

Then, in the container:

.. code:: bash

    python3 -m jupyter notebook --ip="$(hostname -i)" --port=8080

Open the shown link in your host's web browser, navigate to `<examples.ipynb>`_,
and start transpiling!


Related publications
====================

Below is the list of papers describing various aspects of transpyle and/or principles behind it.
Further research is ongoing, so the list might be extended in the future.

*   M. Bysiek, A. Drozd and S. Matsuoka,
    *Migrating Legacy Fortran to Python While Retaining Fortran-Level Performance
    Through Transpilation and Type Hints*,
    PyHPC 2016: 6th Workshop on Python for High-Performance and Scientific Computing @ SC16,
    Salt Lake City, Utah, United States of America, 2016, pp. 9-18

    Abstract:

        We propose a method of accelerating Python code by just-in-time compilation leveraging type
        hints mechanism introduced in Python 3.5. In our approach performance-critical kernels are
        expected to be written as if Python was a strictly typed language, however without the need
        to extend Python syntax. This approach can be applied to any Python application, however we
        focus on a special case when legacy Fortran applications are automatically translated into
        Python for easier maintenance. We developed a framework implementing two-way transpilation
        and achieved performance equivalent to that of Python manually translated to Fortran, and
        better than using other currently available JIT alternatives (up to 5x times faster than
        Numba in some experiments).

    https://doi.org/10.1109/PyHPC.2016.006

*   M. Bysiek, M. Wahib, A. Drozd and S. Matsuoka,
    *Towards Portable High Performance in Python: Transpilation, High-Level IR,
    Code Transformations and Compiler Directives (Unreferred Workshop Manuscript)*,
    2018-HPC-165: 研究報告ハイパフォーマンスコンピューティング,
    Kumamoto, Kumamoto, Japan, 2018, pp. 1-7

    Abstract:

        We present a method for accelerating the execution of Python programs. We rely on
        just-in-time automatic code translation and compilation with Python itself being used as a
        high-level intermediate representation. We also employ performance-oriented code
        transformations and compiler directives to achieve high performance portability while
        enabling end users to keep their codebase in pure Python. To evaluate our method, we
        implement an open-source transpilation framework with an easy-to-use interface that
        achieves performance better than state-of-the-art methods for accelerating Python.

    http://id.nii.ac.jp/1001/00190591/
