import json
import pytest
from fs import open_fs
from fs.wrap import read_only

from cacofonix._app import detect_version, package_json


class TestDetectVersion:
    """
    Tests for `detect_version`.
    """
    never = ('never', lambda _: None)
    always = ('always', lambda _: '1.2.3')

    def test_detect_nothing(self):
        _guesses = [self.never]
        with open_fs('mem://') as cwd_fs:
            assert detect_version(cwd_fs, _guesses) is None

    def test_detect_something(self):
        _guesses = [self.always]
        with open_fs('mem://') as cwd_fs:
            assert detect_version(cwd_fs, _guesses) == (
                'always', '1.2.3')


@pytest.mark.usefixtures('tmpdir')
class TestPackageJson:
    """
    Tests for ``package.json`` version detection.
    """
    def test_nonexistent_file(self, tmpdir):
        with tmpdir.as_cwd():
            with open_fs('.') as cwd_fs:
                assert package_json(read_only(cwd_fs)) is None

    def test_missing_version(self, tmpdir):
        with tmpdir.as_cwd():
            with open_fs('.') as cwd_fs:
                content = json.dumps({'name': 'Test'})
                cwd_fs.writetext('package.json', content)
                assert package_json(read_only(cwd_fs)) is None

    def test_version(self, tmpdir):
        with tmpdir.as_cwd():
            with open_fs('.') as cwd_fs:
                content = json.dumps({'name': 'Test', 'version': '1.2.3'})
                cwd_fs.writetext('package.json', content)
                assert package_json(read_only(cwd_fs)) == '1.2.3'
