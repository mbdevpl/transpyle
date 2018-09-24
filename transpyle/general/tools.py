"""For running external tools in a slightly isolated ."""

import contextlib
import io
import logging
import os
import pathlib
import subprocess

import argunparse

_LOG = logging.getLogger(__name__)


def _postprocess_result(result: subprocess.CompletedProcess) -> None:
    if isinstance(result.stdout, bytes):
        result.stdout = result.stdout.decode('utf-8', 'ignore')
    if isinstance(result.stderr, bytes):
        result.stderr = result.stderr.decode('utf-8', 'ignore')
    if len(result.stderr) > 10240:
        result.stderr = result.stderr[:10240]


@contextlib.contextmanager
def temporarily_change_dir(path: pathlib.Path):
    """If given path is none, it does nothing."""
    if path is None:
        yield
        return
    assert path.is_dir(), path
    _working_dir = pathlib.Path.cwd()
    try:
        os.chdir(str(path))
        yield
    finally:
        os.chdir(str(_working_dir))


@contextlib.contextmanager
def redirect_stdout_and_stderr(stdout, stderr):
    with contextlib.redirect_stdout(stdout):
        with contextlib.redirect_stderr(stderr):
            yield


def run_tool(executable: pathlib.Path, args=(), kwargs=None, wd: pathlib.Path = None,
             argunparser: argunparse.ArgumentUnparser = None) -> subprocess.CompletedProcess:
    """Run a given executable with given arguments."""
    if kwargs is None:
        kwargs = {}
    if argunparser is None:
        argunparser = argunparse.ArgumentUnparser()
    command = [str(executable)] + argunparser.unparse_options_and_args(kwargs, args, to_list=True)
    run_kwargs = {'stdout': subprocess.PIPE, 'stderr': subprocess.PIPE}
    if wd is not None:
        run_kwargs['wd'] = str(wd)
    result = subprocess.run(command, **run_kwargs)
    _LOG.debug('return code of "%s" tool: %s', executable, result)
    _postprocess_result(result)
    if result.returncode != 0:
        _LOG.error('%s', result)
        raise RuntimeError('execution of "{}" failed: {}'.format(executable.name, result))
    return result


def call_tool(function, args=(), kwargs=None, wd: pathlib.Path = None,
              commandline_equivalent: str = None) -> subprocess.CompletedProcess:
    """Call a given function with given arguments and report result as if it was a subprocess.

    Assumption is that the function returns a numeric return code, just as a subprocess would.
    """
    if kwargs is None:
        kwargs = {}
    stdout = io.StringIO()
    stderr = io.StringIO()
    with temporarily_change_dir(wd):
        with redirect_stdout_and_stderr(stdout, stderr):
            returncode = function(*args, **kwargs)
    if commandline_equivalent is None:
        argunparser = argunparse.ArgumentUnparser()
        commandline_equivalent = '{} {}'.format(
            function.__name__, argunparser.unparse_options_and_args(kwargs, args))
    run_results = {'returncode': returncode,
                   'stdout': stdout.getvalue(), 'stderr': stderr.getvalue()}
    if wd is not None:
        run_results['wd'] = str(wd)
    result = subprocess.CompletedProcess(args=commandline_equivalent, **run_results)
    _postprocess_result(result)
    if result.returncode != 0:
        raise RuntimeError('execution of {}() failed: {}'.format(function.__name__, result))
    return result
