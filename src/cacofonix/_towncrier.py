import os
import pkgutil
from towncrier._builder import (
    find_fragments,
    split_fragments,
    render_fragments)
from towncrier._writer import append_to_newsfile
from typing import Iterable, List

from ._util import pluralize
from ._types import Fragment, OutputType
from .errors import InvalidChangeMetadata


class MarkdownRenderer(object):
    def link(self, text, url):
        return f'[{text}]({url})'


class RestructuredTextRenderer(object):
    def link(self, text, url):
        return f'`{text} <{url}>`'


_renderers = {
    'markdown': MarkdownRenderer(),
    'rest': RestructuredTextRenderer(),
}


def _ticket_prefix(ticket):
    """
    Add an appropriate prefix to a ticket number.
    """
    if ticket.isdigit():
        return f'#{ticket}'
    return ticket


def render_fragment(
        fragment: Fragment,
        showcontent: bool,
        output_type: OutputType) -> str:
    """
    Compile a fragment into towncrier-compatible content.
    """
    renderer = _renderers[output_type]
    feature_flag_text = ''
    feature_flags = fragment.get('feature_flags')
    if feature_flags:
        feature_flag_text = ' ({feature}: {flags})'.format(
            feature=pluralize(len(feature_flags),
                              'feature',
                              'features').title(),
            flags=', '.join(u'`{}`'.format(flag) for flag in feature_flags))

    issues_text = ''
    issues = fragment.get('issues')
    if issues:
        issues_text = ' {}'.format(
           u' '.join(
               renderer.link(_ticket_prefix(ticket), url)
               for ticket, url in sorted(issues.items())))

    description_first_text = ''
    description_rest_text = ''
    description = fragment.get('description')
    if description:
        desc_lines = description.split('\n')
        description_first_text = desc_lines[0]
        description_rest_text = '{}{}'.format(
            '\n' if len(desc_lines) > 1 else u'',
            '\n'.join(desc_lines[1:])).rstrip()
    else:
        raise InvalidChangeMetadata('Missing change description')

    if not showcontent:
        return issues_text
    return ''.join([
        description_first_text,
        feature_flag_text,
        issues_text,
        description_rest_text,
    ])


def render_changelog(
        fragment_path: str,
        output_type: OutputType,
        sections: Iterable[str],
        fragment_types: Iterable[str],
        underlines: List[str],
        project_version: str,
        project_date: str):
    """
    Render change fragments into a new partial changelog.

    This changelog can be merged into an existing changelog with
    `merge_with_existing_changelog`.
    """
    fragments, fragment_filenames = find_fragments(
        fragment_path,
        sections,
        None,
        fragment_types)
    fragments = split_fragments(fragments, fragment_types)
    template_name = (
        'templates/towncrier_markdown.tmpl' if output_type == 'markdown' else
        'templates/towncrier_rest.tmpl')
    template = pkgutil.get_data(__name__, template_name).decode('utf-8')
    issue_format = ''
    top_line = ''
    wrap = False
    return render_fragments(
        template,
        issue_format,
        top_line,
        fragments,
        fragment_types,
        underlines,
        wrap,
        {'name': '',
         'version': project_version,
         'date': project_date},
        top_underline=underlines[0])


def merge_with_existing_changelog(
        changelog_path: str,
        changelog_marker: str,
        content: str):
    """
    Merge new changelog content with an existing changelog.

    The new content will be placed below `changelog_marker` in the existing
    changelog.
    """
    # TODO: Detect existing changelog for this change, since towncrier
    # is broken.
    top_line, content = content.split('\n', 1)
    append_to_newsfile(
        os.getcwd(),
        changelog_path,
        changelog_marker,
        top_line + '\n',
        content,
        single_file=True)
