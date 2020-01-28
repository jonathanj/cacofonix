import os
from typing import Iterable, List, Optional, TextIO, Tuple

from . import _yaml
from ._config import Config
from .errors import InvalidChangeMetadata, FragmentCompilationError
from ._util import ensure_parent_exists
from ._towncrier import (
    render_fragment,
    render_changelog,
    merge_with_existing_changelog)
from ._types import Fragment


class Application(object):
    def __init__(self, config: Config):
        self.config = config

    def load_fragment(self, fd: TextIO) -> Fragment:
        return self.validate_fragment(_yaml.load(fd))

    def find_fragments(self) -> Iterable[Tuple[str, List[str]]]:
        """
        """
        fragments_path = self.config.change_fragments_path
        for dirpath, dirnames, filenames in os.walk(fragments_path):
            yield (
                None if dirpath == fragments_path else dirpath,
                [os.path.join(dirpath, filename)
                 for filename in filenames
                 if os.path.splitext(filename)[-1] == '.yaml'])

    def find_all_fragments(self) -> Iterable[str]:
        """
        Find all fragment files in the config value `change_fragments_path`.
        """
        for dirpath, filepaths in self.find_fragments():
            for path in filepaths:
                yield path

    def remove_fragments(self) -> Tuple[int, List[str]]:
        """
        Remove all fragment files in the config value `change_fragments_path`.
        """
        not_removed = []
        n = 0
        for n, (dirname, filepaths) in enumerate(self.find_fragments()):
            for path in filepaths:
                try:
                    os.remove(path)
                except (OSError, FileNotFoundError):
                    not_removed.append(path)
            if dirname is not None:
                try:
                    os.rmdir(dirname)
                except (OSError, FileNotFoundError):
                    not_removed.append(dirname)
        return n, not_removed

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

        return fragment

    def compile_fragment_files(self, parent_dir: str,
                               fragment_paths: List[str]) -> int:
        """
        Compile fragment files into `parent_dir`.
        """
        n = 0
        for n, fragment_path in enumerate(fragment_paths, 1):
            with open(fragment_path, 'rb') as fd:
                try:
                    fragment = self.load_fragment(fd)
                    fragment_type = fragment.get('type')
                    section = fragment.get('section') or None
                    filename = os.path.splitext(
                        os.path.basename(fragment_path))[0]
                    output_path = os.path.join(
                        parent_dir,
                        *filter(None, [
                            section,
                            '{}.{}'.format(filename, fragment_type)]))
                    with open(ensure_parent_exists(output_path), 'w') as fd:
                        fd.write(render_fragment(fragment))
                except Exception:
                    raise FragmentCompilationError(fragment_path)
        return n

    def render_changelog(
            self,
            parent_dir: str,
            project_version: str,
            project_date: str) -> str:
        """
        Find compiled fragments in `parent_dir` and render a changelog with
        them.
        """
        return render_changelog(
            parent_dir,
            self.config.changelog_output_type,
            self.config.sections,
            self.config.fragment_types,
            self.config._towncrier_underlines(),
            project_version=project_version,
            project_date=project_date)

    def merge_with_existing_changelog(self, changelog: str) -> None:
        """
        Merge a new changelog into an existing one.
        """
        return merge_with_existing_changelog(
            self.config.changelog_path,
            self.config.changelog_marker,
            changelog)
