"""Configuration mechanisms for transpyle."""

# import copy
import datetime
import logging
import logging.config
import pathlib
import platform
import typing as t

import colorama
from encrypted_config import normalize_path

_LOG = logging.getLogger(__name__)

PACKAGE_ROOT_PATH = pathlib.Path(__file__).resolve().parent

APP_DIRNAME = 'transpyle'

CONFIG_PATHS = {
    'Linux': pathlib.Path('~', '.config', APP_DIRNAME),
    'Darwin': pathlib.Path('~', 'Library', 'Preferences', APP_DIRNAME),
    'Windows': pathlib.Path('%LOCALAPPDATA%', APP_DIRNAME)}

CONFIG_PATH = CONFIG_PATHS[platform.system()]

LOGTS_PATHS = {
    'Linux': pathlib.Path('~', '.local', 'share', APP_DIRNAME),
    'Darwin': pathlib.Path('~', 'Library', 'Logs', APP_DIRNAME),
    # TODO: where to store logs on Windows?
    # 'Windows': pathlib.Path('%LOCALAPPDATA%', APP_DIRNAME)
    }

LOGS_PATH = LOGTS_PATHS[platform.system()]


def logging_level_from_envvar(envvar: str, default: int = logging.WARNING) -> int:
    """Translate text envvar into an integer corresponding to a logging level."""
    import os

    envvar_value = os.environ.get(envvar)
    if envvar_value is None:
        return default
    envvar_value = envvar_value.upper()
    if not hasattr(logging, envvar_value):
        try:
            return int(envvar_value)
        except ValueError:
            return default
    return getattr(logging, envvar_value)


# PROJECT_ROOT_PATH = _HERE.parent

# TEST_ROOT_PATH = PROJECT_ROOT_PATH.joinpath('test')

# TEST_RESULTS_ROOT_PATH = TEST_ROOT_PATH.joinpath('results')

# LOGS_PATH_TESTS =

# LOGGING_CONFIG_TESTS = copy.deepcopy(LOGGING_CONFIG)

# LOGGING_CONFIG_TESTS['handlers']['file']['filename'] = str(pathlib.Path())


def unittest_verbosity() -> t.Optional[int]:
    """Retrieve the verbosity setting of the currently running unittest program.

    Return None if currently running program is not unittest.

    Default verbosity level is 1, 0 means quiet and 2 means verbose.
    """
    import inspect
    import unittest

    frame = inspect.currentframe()
    while frame:
        self_ = frame.f_locals.get('self')
        if isinstance(self_, unittest.TestProgram):
            return self_.verbosity
        frame = frame.f_back
    return None


def configure_logging():
    log_filename = 'transpyle-{}.log'.format(datetime.datetime.now().strftime(r'%Y%m%d-%H%M%S'))
    logging_config = {
        'formatters': {
            'brief': {
                '()': 'colorlog.ColoredFormatter',
                'style': '{',
                'format': '{name} [{log_color}{levelname}{reset}] {message}'},
            'precise': {
                'style': '{',
                'format': '{asctime} {name} [{levelname}] {message}'}},
        'handlers': {
            'console': {
                'class': 'logging.StreamHandler',
                'formatter': 'brief',
                'level': logging_level_from_envvar('LOGGING_LEVEL', default=logging.WARNING),
                'stream': 'ext://sys.stdout'},
            'file': {
                'class': 'logging.handlers.RotatingFileHandler',
                'formatter': 'precise',
                'level': logging.NOTSET,
                'filename': normalize_path(str(LOGS_PATH.joinpath(log_filename))),
                'maxBytes': 1 * 1024 * 1024,
                'backupCount': 10}},
        'root': {
            'handlers': ['console', 'file'],
            'level': logging.NOTSET},
        'version': 1,
        'disable_existing_loggers': False}
    logging.config.dictConfig(logging_config)


def configure_basic_logging():
    # logging.basicConfig(level=logging.DEBUG)
    # logging.basicConfig(level=logging.INFO)
    log_filename = 'transpyle-{}.log'.format(datetime.datetime.now().strftime(r'%Y%m%d'))
    logging.basicConfig(
        level=logging_level_from_envvar('LOGGING_LEVEL', default=logging.WARNING),
        filename=normalize_path(str(LOGS_PATH.joinpath(log_filename))))


def configure(quick: bool = False):
    colorama.init()

    config_path = normalize_path(CONFIG_PATH)
    if not config_path.is_dir():
        config_path.mkdir(parents=True)
    logs_path = normalize_path(LOGS_PATH)
    if not logs_path.is_dir():
        logs_path.mkdir(parents=True)

    if quick:
        configure_basic_logging()
        return

    # try:
    #     import git
    #     git.Repo(str(PROJECT_ROOT_PATH), search_parent_directories=True)
    #     running_from_repo = True
    # except git.exc.InvalidGitRepositoryError:
    #     running_from_repo = False
    # unittest_verbosity = unittest_verbosity()
    configure_logging()
