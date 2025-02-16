"""Parsing C++."""

import logging
import pathlib
import platform
import tempfile
import xml.etree.ElementTree as ET

import argunparse
import version_query

from ..general import ExternalTool, Parser
from ..general.exc import ExternalToolVersionError
from ..general.tools import run_tool

_LOG = logging.getLogger(__name__)


class CastXml(ExternalTool):
    """Define how to execute CastXML tool.

    https://github.com/CastXML/CastXML
    """

    path = pathlib.Path('castxml')
    _version_arg = '--version'

    @classmethod
    def _version_output_filter(cls, output: str) -> str:
        for output_line in output.splitlines():
            if output_line.startswith('castxml version '):
                return output_line.replace('castxml version ', '')
        raise ExternalToolVersionError(f'could not extract version from output: {output}')


CastXml.assert_version_at_least(version_query.Version(0, 4))


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
    return run_tool(CastXml.path, args, kwargs,
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
