import os.path
import pytest
from fs import open_fs
from fs.base import FS
from fs.wrap import read_only

from cacofonix._app import Application
from cacofonix._config import Config
from cacofonix._effects import SideEffects


class MockSideEffects(SideEffects):
    def __init__(self, root_fs, config):
        self.root_fs = root_fs
        self.fragments_fs = self.root_fs.opendir(config.change_fragments_path)

    def archive_fs(self, path: str) -> FS:
        raise NotImplementedError()

    def changelog_fs(self, path: str) -> FS:
        raise NotImplementedError()

    def git_mv(self, path: str) -> FS:
        raise NotImplementedError()

    def git_stage(self, path: str) -> FS:
        raise NotImplementedError()


def open_test_root_fs() -> FS:
    """
    Open the filesystem root for the tests.
    """
    cwd = os.path.dirname(__file__)
    return read_only(open_fs('data', cwd=cwd))


def load_test_config(root_fs) -> Config:
    """
    Load the config files for the tests.
    """
    with root_fs.open('config.yaml') as fd:
        return Config.parse(fd)


class TestCompileFragmentFiles:
    """
    Tests for `Application.compile_fragment_files`.
    """
    def test_numeric_issue_key(self):
        """
        Issues with numeric keys can be compiled.
        """
        with open_test_root_fs() as root_fs:
            config = load_test_config(root_fs)
            effects = MockSideEffects(root_fs, config)
            app = Application(config, effects)
            found_fragments = [
                (effects.fragments_fs, 'numeric_issue_number.yaml'),
            ]
            with open_fs('temp://') as write_fs:
                outputs = app.compile_fragment_files(
                    write_fs,
                    found_fragments)
                assert len(outputs) == 1
                assert '#1234' in write_fs.readtext(outputs[0])
