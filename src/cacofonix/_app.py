import json
import secrets
import time
from datetime import date
from fs.base import FS
from fs.path import join, dirname, basename, splitext
from semver import VersionInfo, parse_version_info
from typing import (
    Iterable,
    List,
    Optional,
    TextIO,
    Tuple,
    Union)

from . import _yaml, _log as log
from ._config import Config
from .errors import InvalidChangeMetadata, FragmentCompilationError
from ._towncrier import (
    render_fragment,
    render_changelog,
    merge_with_existing_changelog)
from ._types import Fragment, FoundFragment, GuessPair
from ._effects import SideEffects


class Application(object):
    METADATA_FILENAME: str = 'metadata.yaml'

    def __init__(self, config: Config, effects: SideEffects):
        self.config = config
        self.effects = effects
        fragments_path = effects.fragments_fs.getsyspath('.')
        log.debug(f'Fragments root: {fragments_path}')

    def load_fragment(self, fd: TextIO) -> Fragment:
        """
        Parse and validate a fragment from a stream.
        """
        return self.validate_fragment(_yaml.load(fd))

    def find_fragments(
            self,
            version: Union[str, VersionInfo]
    ) -> Iterable[FoundFragment]:
        """
        Find all fragments for a particular verison.
        """
        log.debug(f'Finding fragments for version {version}')
        version_fs = self.effects.fragments_fs.opendir(str(version))
        matches = version_fs.filterdir(
            '.',
            files=['*.yaml'],
            exclude_files=[self.METADATA_FILENAME])
        for file_info in matches:
            file_path = file_info.name
            log.debug(f'Found {file_path}')
            yield version_fs, file_path

    def find_new_fragments(self) -> Iterable[FoundFragment]:
        """
        Find fragment files for the next version.
        """
        return self.find_fragments('next')

    def archive_fragments(
            self,
            found_fragments: Iterable[FoundFragment],
            version: VersionInfo,
            version_date: date,
            version_author: str,
    ) -> Tuple[int, List[str]]:
        """
        Archive new fragment, into the path for ``version``.
        """
        problems = []
        n = 0
        with self.effects.archive_fs(str(version)) as archive_fs:
            log.info(f'Archiving for {version}')
            for n, (version_fs, filename) in enumerate(found_fragments, 1):
                try:
                    path = version_fs.getsyspath(filename)
                    archive_path = archive_fs.getsyspath(filename)
                    log.info(f'Archive {path} -> {archive_path}')
                    self.effects.git_mv(path, archive_path)
                    self.effects.git_stage(archive_path)
                except (OSError, FileNotFoundError):
                    log.exception(
                        f'Unable to archive fragment: {version_fs} {filename}')
                    problems.append(path)

            if not problems:
                log.info('Writing archival metadata')
                metadata = {
                    'date': version_date,
                    'version': str(version),
                    'author': version_author}
                log.debug(metadata)
                archive_fs.settext(
                    self.METADATA_FILENAME, _yaml.dump(metadata))
                metadata_path = archive_fs.getsyspath(self.METADATA_FILENAME)
                self.effects.git_stage(metadata_path)

        return n, problems

    def create_new_fragment(self, yaml_text: str) -> str:
        """
        Generate a unique filename for a fragment, and write the content to it.
        """
        filename = '{}-{}.yaml'.format(
            int(time.time() * 1000),
            secrets.token_urlsafe(6))
        with self.effects.archive_fs('next') as next_fs:
            if next_fs.exists(filename):
                raise RuntimeError(
                    'Generated fragment name already exists!', filename)
            path = next_fs.getsyspath(filename)
            log.debug(f'Writing new fragment {path}')
            next_fs.settext(filename, yaml_text)
            self.effects.git_stage(path)
            return filename

    def validate_fragment(self, fragment: Optional[Fragment]) -> Fragment:
        """
        Validate change fragment data.

        Fragments must have some value (not empty) and must have a known
        fragment type and section.
        """
        if fragment is None:
            raise InvalidChangeMetadata('No data to parse')

        fragment_type = fragment.get('type')
        if not self.config.has_fragment_type(fragment_type):
            raise InvalidChangeMetadata(
                'Missing or unknown fragment type', fragment_type)
        section = fragment.get('section') or None
        if section and not self.config.has_section(section):
            raise InvalidChangeMetadata(
                'Missing or unknown section', section)
        description = fragment.get('description')
        if description is None or not description.strip():
            raise InvalidChangeMetadata(
                'Missing a change description')
        return fragment

    def validate_fragment_text(self, fragment_text: Optional[str]) -> None:
        """
        Validate change fragment text.
        """
        fragment = _yaml.load(fragment_text)
        self.validate_fragment(fragment)

    def compile_fragment_files(
            self,
            write_fs: FS,
            found_fragments: Iterable[FoundFragment]) -> int:
        """
        Compile fragment files into `parent_dir`.
        """
        n = 0
        for n, (version_fs, filename) in enumerate(found_fragments, 1):
            try:
                fragment = self.load_fragment(version_fs.readtext(filename))
                fragment_type = fragment.get('type')
                showcontent = self.config.fragment_types.get(
                    fragment_type, {}).get('showcontent', True)
                section = fragment.get('section') or None
                rendered_content = render_fragment(
                    fragment,
                    showcontent,
                    self.config.changelog_output_type)
                if rendered_content.strip():
                    filename_stem = splitext(basename(filename))[0]
                    output_path = join(*filter(None, [
                        section,
                        '{}.{}'.format(filename_stem, fragment_type)]))
                    log.info(
                        'Compiling {} -> {}'.format(
                            version_fs.getsyspath(filename),
                            write_fs.getsyspath(output_path)))
                    parent_dir = dirname(output_path)
                    if parent_dir:
                        write_fs.makedirs(parent_dir, recreate=True)
                    write_fs.writetext(output_path, rendered_content)
            except Exception:
                raise FragmentCompilationError(filename)
        return n

    def render_changelog(
            self,
            fs: FS,
            version: VersionInfo,
            version_date: date) -> str:
        """
        Find compiled fragments in `parent_dir` and render a changelog with
        them.
        """
        parent_dir = fs.getsyspath('.')
        return render_changelog(
            parent_dir,
            self.config.changelog_output_type,
            self.config._towncrier_sections(parent_dir),
            self.config._towncrier_fragment_types(),
            self.config._towncrier_underlines(),
            project_version=str(version),
            project_date=version_date.isoformat())

    def merge_with_existing_changelog(self, changelog: str) -> None:
        """
        Merge a new changelog into an existing one.
        """
        with self.effects.changelog_fs() as changelog_fs:
            changelog_path = changelog_fs.getsyspath(
                self.config.changelog_path)
            merge_with_existing_changelog(
                changelog_path,
                self.config.changelog_marker,
                changelog)
            self.effects.git_stage(changelog_path)

    def guess_version(self, cwd_fs: FS) -> Optional[str]:
        """
        Attempt to guess the software version.
        """
        return detect_version(cwd_fs)

    def known_versions(self) -> List[VersionInfo]:
        """
        Sorted list of archived versions.
        """
        fragments_fs = self.effects.fragments_fs
        return sorted(
            (parse_version_info(info.name) for info in
             fragments_fs.filterdir(
                 '.',
                 exclude_files=['*'],
                 exclude_dirs=['next'])),
            reverse=True)


def package_json(cwd_fs: FS):
    """
    Try guess a version from ``package.json``.
    """
    log.debug('Looking for package.json')
    if cwd_fs.exists('package.json'):
        log.debug('Guessing version with package.json')
        try:
            with cwd_fs.open('package.json', 'r') as fd:
                return json.load(fd).get('version')
        except json.JSONDecodeError:
            pass
    return None


_default_guesses = [
    ('package.json', package_json),
]


def detect_version(cwd_fs: FS, _guesses: List[GuessPair]) -> Optional[str]:
    """
    Make several attempts to guess the version of the package.
    """
    for kind, guess in _guesses:
        result = guess(cwd_fs)
        if result is not None:
            return kind, result
    return None
