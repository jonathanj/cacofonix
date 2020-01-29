import os
from collections import OrderedDict
from typing import TextIO, Iterable, Optional, TypeVar, Container

from . import _yaml


T = TypeVar('T')

default_sections = OrderedDict([('', '')])

default_fragment_types = OrderedDict([
    (u'feature', {'name': u'Added', 'showcontent': True}),
    (u'bugfix', {'name': u'Fixed', 'showcontent': True}),
    (u'doc', {'name': u'Documentation', 'showcontent': True}),
    (u'removal', {'name': u'Removed', 'showcontent': True}),
    (u'misc', {'name': u'Misc', 'showcontent': False}),
])


def validate_defined(value: Optional[T], hint=None) -> T:
    """
    Validate that a value is defined, if given, exists.
    """
    if value is None:
        raise ValueError('Nonexistent or missing value', value, hint)
    return value


def validate_oneof(
        value: Optional[T],
        container: Container[T],
        hint=None) -> T:
    """
    Validate that a value is one of a set of values.
    """
    if value is None or value not in container:
        raise ValueError(
            'Expecting value to be one of', container, value, hint)
    return value


class Config(object):
    """
    Configuration options.
    """
    __slots__ = [
        'change_fragments_path',
        'changelog_path',
        'changelog_marker',
        'changelog_output_type',
        'sections',
        'fragment_types',
    ]

    def __init__(self, **kw):
        super(Config, self).__init__()
        for key, val in kw.items():
            setattr(self, key, val)

    def __repr__(self):
        obj = {key: getattr(self, key) for key in self.__slots__}
        return repr(obj)

    @classmethod
    def parse(cls, fd: TextIO) -> 'Config':
        """
        Parse a YAML config.
        """
        def make_fragment_type(title, showcontent=True):
            return {'name': title, 'showcontent': showcontent}

        config = _yaml.load(fd)
        config['changelog_marker'] = config.setdefault(
            'changelog_marker',
            '<!-- Generated release notes start. -->')
        config['fragment_types'] = OrderedDict([
            (key, make_fragment_type(**fragment_type)) for
            key, fragment_type in
            config.get('fragment_types', default_fragment_types).items()
        ])
        config['changelog_output_type'] = validate_oneof(
            config.get('changelog_output_type', 'markdown'),
            {'markdown', 'rest'})
        validate_defined(config.get('changelog_path'),
                         'changelog_path')
        validate_defined(config.get('change_fragments_path'),
                         'change_fragments_path')

        sections = default_sections.copy()
        sections.update([
            (title, dirname) for dirname, title
            in (config.get('sections') or {}).items()])
        config['sections'] = sections
        return Config(**config)

    def available_sections(self) -> Iterable[str]:
        """
        Names of available section keys.
        """
        return self.sections.values()

    def has_section(self, section: str) -> bool:
        """
        Does this configuration specify a section named by `section`?
        """
        return section in self.available_sections()

    def available_fragment_types(self) -> Iterable[str]:
        """
        Names of available fragment types.
        """
        return self.fragment_types.keys()

    def has_fragment_type(self, fragment_type: str) -> bool:
        """
        Does this configuration specify a fragment type named by
        `fragment_type`?
        """
        return fragment_type in self.available_fragment_types()

    def _towncrier_underlines(self):
        """
        Pick a suitable underline set for towncrier, based on the output type.
        """
        return {
            'markdown': ['##', '###', '####'],
            'rest': ['=', '-', '~'],
        }[self.changelog_output_type]

    def _towncrier_fragment_types(self):
        """
        Generate a `fragment_types` structure for towncrier.
        """
        def _fix_showcontent(d):
            d['showcontent'] = True
            return d
        return {
            key: _fix_showcontent(val)
            for key, val in self.fragment_types.items()}

    def _towncrier_sections(self):
        """
        Generate a `sections` structure for towncrier.
        """
        change_fragments_path = self.change_fragments_path
        return {path: title for path, title in
                self.sections.items()
                if os.path.exists(os.path.join(change_fragments_path, path))}
