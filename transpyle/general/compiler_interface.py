"""An interface to a standard compiler."""

# import itertools
import logging
import pathlib
import typing as t

from .tools import run_tool
from .compiler import Compiler

_LOG = logging.getLogger(__name__)


class CompilerInterface(Compiler):

    """Interface to one of the standard compilers.

    Such compilers need several separate steps, as defined in "step_names" field.

    A step named 'abc' will cause method '_abc' to be called in order with the following arguments:

    """

    step_names = ['compile', 'link']  # type: t.List[str]

    _features = set()
    """List of strings indicating a supported feature of the compiler.

    Feature name cannot be the same as name of any compiler step.
    """

    _executables = {}  # type: t.Dict[str, pathlib.Path]
    """Paths to executables used in each step of compilation.

    Use '' (empty string) as name to indicate that executable name is the same in all steps.

    Use feature name as name to indicate that executable is to be used if a feature is enabled.

    Use 'step_feature' as name to set executable used at specific step in a feature is enabled.
    """

    _flags = {}  # type: t.Dict[str, t.Sequence[str]]
    """Flags used in each step of compilation.

    The same rules apply for step naming as with executables.
    """

    _options = {}
    """Options used in each step of compilation.

    The same rules apply for step naming as with executables.
    """

    def __init__(self, features: t.Set[str] = None, *args, **kwargs):
        assert all(_ not in self.step_names for _ in self._features), 'features and steps overlap'
        # assert all(_ not in self._features for _ in self.step_names)
        # TODO: validate executables and flags dictionaries
        super().__init__(*args, **kwargs)
        if features is None:
            features = set()
        for feature in features:
            if feature not in self._features:
                raise ValueError('Feature "{}" is not supported by {}'.format(feature, self))
        self.features = features
        _LOG.debug('initialized compiler interface %s with enabled features=%s', self, features)

    def _get_value(self, field, step_name) -> t.Any:
        for feature in self.features:
            step_feature = '{}_{}'.format(step_name, feature)
            if step_feature in field:
                return field[step_feature]
            if feature in field:
                return field[feature]
        if step_name in field:
            return field[step_name]
        return field['']

    def executable(self, step_name) -> pathlib.Path:
        return self._get_value(self._executables, step_name)

    def _create_list(self, field, step_name) -> t.List[t.Any]:
        list_ = []
        if '' in field:
            list_ += field['']
        if step_name in field:
            list_ += field[step_name]
        for feature in self.features:
            if feature in field:
                list_ += field[feature]
            step_faeture = '{}_{}'.format(step_name, feature)
            if step_faeture in field:
                list_ += field[step_faeture]
        return list_

    def flags(self, step_name) -> t.List[str]:
        return self._create_list(self._flags, step_name)

    def options(self, step_name):
        return self._create_list(self._options, step_name)

    def compile(self, code: str, path: t.Optional[pathlib.Path] = None,
                output_folder: t.Optional[pathlib.Path] = None, **kwargs) -> pathlib.Path:
        step_output = {}
        for step_name in self.step_names:
            step = getattr(self, '_{}'.format(step_name))
            # if previous_step_result:
            #    args.append(previous_step_result)
            step_output = step(code, path, output_folder, **kwargs, **step_output)
        return step_output

    def _compile(self, code, path, output_folder, input_paths: t.Sequence[pathlib.Path], **kwargs):
        result = run_tool(self.executable('compile'), [
            *self.flags('compile'), *self.options('compile'),
            '-c', *[str(path) for path in input_paths]])
        return {'results': {'compile': result}}

    def _link(self, code, path, output_folder, input_paths: t.Sequence[pathlib.Path],
              output_path: pathlib.Path, **kwargs):
        input_paths = [path.with_suffix('.o') for path in input_paths]
        result = run_tool(self.executable('link'), [
            *self.flags('link'), *self.options('link'),
            '-shared', *[str(path) for path in input_paths], '-o', str(output_path)])
        return {'results': {'link': result, **kwargs['results']}}
