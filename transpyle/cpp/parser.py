"""Parsing C++."""

import logging
import pathlib
import subprocess
import tempfile
import xml.etree.ElementTree as ET

from ..general import Parser

_LOG = logging.getLogger(__name__)


def run_castxml(input_path: pathlib.Path, output_path: pathlib.Path, gcc: bool = False):
    """Run CastXML with given arguments"""
    castxml = pathlib.Path('castxml')
    output_version = '--castxml-gccxml' if gcc else '--castxml-output=1'
    result = subprocess.run(
        [str(castxml), output_version, '-o', str(output_path), str(input_path)],
        stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    if result.returncode != 0:
        _LOG.error('%s', result)
        raise RuntimeError('could not parse {}'.format(input_path))
    return result


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
