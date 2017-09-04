"""transpyle package."""

import pathlib
import sys

try:
    import static_typing
except ImportError:
    path = pathlib.Path('~', 'Projects', 'python', 'static-typing').expanduser()
    sys.path.append(str(path))
    import static_typing
