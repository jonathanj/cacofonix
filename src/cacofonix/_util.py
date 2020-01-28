import os
import shutil
import tempfile
from codecs import encode, decode
from subprocess import check_call


def pluralize(n: int, singular: str, plural: str) -> str:
    """
    Use the plural or singular form based on some count.
    """
    return singular if n == 1 else plural


def string_escape(s: str) -> str:
    """
    Like `.decode('string-escape')` in Python 2 but harder because Python 3.
    """
    return decode(encode(s, 'latin-1', 'backslashreplace'), 'unicode-escape')


def git_stage(path: str) -> None:
    """
    Stage `path` in git.
    """
    check_call(['git', 'add', path])


class TemporaryDirectory(object):
    """
    Context manager that will create and destroy a temporary directory.
    """
    def __enter__(self):
        self.path = tempfile.mkdtemp(prefix='bard')
        return self.path

    def __exit__(self, exc_type, exc_val, exc_tb):
        shutil.rmtree(self.path)
        self.path = None


def ensure_parent_exists(path: str) -> str:
    """
    Ensure that the parent of `path` exists, creating it and all subdirectories
    if necessary.
    """
    dirname = os.path.dirname(path)
    if not os.path.exists(dirname):
        os.makedirs(dirname)
    return path
