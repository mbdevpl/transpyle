"""Parsing C++."""

import logging
import pathlib
import platform
import tempfile
import xml.etree.ElementTree as ET

import argunparse

from ..general import Parser
from ..general.tools import run_tool

_LOG = logging.getLogger(__name__)

CASTXML_PATH = pathlib.Path('castxml')


def run_castxml(input_path: pathlib.Path, output_path: pathlib.Path, gcc: bool = False):
    """Run CastXML with given arguments."""
    args = ['-std=c++17', '-fcolor-diagnostics', input_path]
    kwargs = {}
    if gcc:
        kwargs['castxml-gccxml'] = True
    else:
        kwargs['castxml-output=1'] = True
    if platform.system() == 'Linux':
        kwargs['castxml-cc-gnu'] = 'g++'
    elif platform.system() == 'Darwin':
        kwargs['castxml-cc-gnu'] = 'clang++'
    kwargs['o'] = str(output_path)
    return run_tool(CASTXML_PATH, args, kwargs,
                    argunparser=argunparse.ArgumentUnparser(opt_value=' '))


class CppParser(Parser):

    """C++ parser using CastXML."""

    def _parse_scope(self, code, path=None):
        output_path = None
        with tempfile.NamedTemporaryFile(delete=False) as temporary_file:
            output_path = pathlib.Path(temporary_file.name)
        _ = run_castxml(path, output_path, gcc=False)
        with open(str(output_path)) as output_file:
            output = output_file.read()
        output_path.unlink()
        return ET.fromstring(output)
