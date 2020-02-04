from abc import ABC, abstractmethod
from fs import open_fs
from fs.base import FS
from fs.wrap import read_only
from subprocess import check_call, check_output
from typing import Optional

from . import _log as log
from ._config import Config


class SideEffects(ABC):
    """
    Abstract side effects class.
    """
    root_fs: FS
    fragments_fs: FS

    def __init__(self, root_fs):
        self.root_fs = root_fs

    @abstractmethod
    def archive_fs(self, path: str) -> FS:
        """
        Generate an FS for an archival version.
        """

    @abstractmethod
    def changelog_fs(self) -> FS:
        """
        Generate an FS for where the changelog resides.
        """
        # TODO: This is not ideal, since it allows access to the rest of the
        # directory too.

    def cwd_fs(self) -> FS:
        """
        Read-only version of the current working directory.
        """
        return read_only(self.root_fs)

    def git_user(self) -> Optional[str]:
        """
        ``git config user.name`` and ``git config user.email``.
        """
        username = check_output(
            ['git', 'config', 'user.name'], text=True).strip()
        email = check_output(
            ['git', 'config', 'user.email'], text=True).strip()
        if not username and not email:
            return None

        if not email:
            return username
        elif not username:
            return f'<{email}>'
        return f'{username} <{email}>'

    @abstractmethod
    def git_mv(self, src: str, dst: str) -> None:
        """
        ``git mv <src> <dst>``
        """

    @abstractmethod
    def git_stage(self, src: str) -> None:
        """
        ``git stage <src>``
        """


class RealSideEffects(SideEffects):
    """
    Perform real side effects that change things like git repositories and
    filesystems.
    """
    def __init__(self, root_fs: FS, config: Config):
        super(RealSideEffects, self).__init__(root_fs)
        self.fragments_fs = root_fs.makedir(
            config.change_fragments_path,
            recreate=True)

    def archive_fs(self, path: str) -> FS:
        return self.fragments_fs.makedir(path, recreate=True)

    def changelog_fs(self) -> FS:
        return self.root_fs.opendir('.')

    def git_mv(self, src, dst):
        check_call(['git', 'mv', src, dst])

    def git_stage(self, src):
        check_call(['git', 'add', src])


def _dry_run_method(name: str):
    """
    Create a dry run stub that logs the action it would have taken.
    """
    def _func(self, *a, **kw):
        log.info(
            'Dry run of {}: {} {}'.format(
                name,
                ' '.join(map(repr, a)),
                ' '.join(f'{key}={repr(value)}' for key, value in kw.items())))
    return _func


class DryRunSideEffects(SideEffects):
    """
    Dry run side effects that change only temporary files or log actions instead
    of performing them.
    """
    git_mv = _dry_run_method('git_mv')
    git_stage = _dry_run_method('git_stage')

    def __init__(self, root_fs: FS, config: Config):
        super(DryRunSideEffects, self).__init__(root_fs)
        self.fragments_fs = read_only(
            root_fs.opendir(config.change_fragments_path))

    def archive_fs(self, path: str) -> FS:
        return open_fs('temp://')

    def changelog_fs(self) -> FS:
        return open_fs('temp://')


def make_effects(root_fs: FS, config: Config, dry_run: bool) -> SideEffects:
    """
    Make the most appropriate ``SideEffects`` instance.
    """
    Effects = DryRunSideEffects if dry_run else RealSideEffects
    return Effects(root_fs, config)
