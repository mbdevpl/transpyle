"""Compiling Fortran code."""

import datetime
import logging
import pathlib
import tempfile
import typing as t

import argunparse

from ..general import Compiler
from ..general.tools import temporarily_change_dir
from .compiler_interface import F2pyInterface

_LOG = logging.getLogger(__name__)


def create_f2py_module_name(path: pathlib.Path) -> str:
    return '{}_transpyle_{}'.format(path.stem, datetime.datetime.now().strftime('%Y%m%d%H%M%S'))


class F2PyCompiler(Compiler):

    """Compile Fortran code into Python extension modules using f2py."""

    def __init__(self, f_compiler=None, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.argunparser = argunparse.ArgumentUnparser()
        self.f2py = F2pyInterface(f_compiler)

    def compile(self, code: str, path: t.Optional[pathlib.Path] = None,
                output_folder: t.Optional[pathlib.Path] = None, **kwargs) -> pathlib.Path:
        """Compile Fortran code using f2py."""
        # kwargs |= self.default_kwargs
        if output_folder is None:
            with tempfile.TemporaryDirectory() as tmpdir:
                output_folder = pathlib.Path(tmpdir)
            output_folder.mkdir()

        assert isinstance(code, str), type(code)
        assert isinstance(path, pathlib.Path), type(path)
        assert path.is_file(), path
        assert isinstance(output_folder, pathlib.Path), type(output_folder)
        assert output_folder.is_dir(), output_folder

        module_name = create_f2py_module_name(path)
        _LOG.debug('f2py desired module name: %s', module_name)

        with temporarily_change_dir(output_folder):
            result = self.f2py.compile(code, path, output_folder, module_name=module_name)

        path_mask = '{}*'.format(module_name)
        output_paths = [output_path for output_path in output_folder.glob(path_mask)
                        if output_path.is_file()]
        if len(output_paths) != 1:
            raise ValueError(
                'expected 1 output path matching "{}" but {} found: {}\nf2py result: {}'
                .format(path_mask, len(output_paths), output_paths, result['result']))
        return output_paths[0]
