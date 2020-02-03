import click
from aniso8601 import parse_date
from collections import OrderedDict
from datetime import date
from semver import VersionInfo, parse_version_info
from typing import Iterable, Optional

from ._app import Application
from ._prompt import (
    prompt_choice,
    prompt_feature_flag,
    prompt_issue,
    prompt_many,
    prompt_markdown,
    required)


def iso8601date(ctx, param, value):
    """
    Accept an ISO8601 date (YYYY-MM-DD), or use today's date if a value is not
    given.
    """
    if value is None:
        return date.today()
    return parse_date(value)


def split_issues(ctx, param, value):
    """
    Split issue arguments into number and URL components.
    """
    def _split_one(value):
        parts = [x.strip() for x in value.split(':', 1) if x.strip()]
        if len(parts) < 1:
            raise click.BadParameter(
                'Invalid issue format, should be issue_number or '
                'issue_number:issue_url')
        elif len(parts) < 2:
            parts = parts + ['ISSUE_URL_HERE']
        return tuple(parts)
    return [_split_one(v) for v in value]


def validate_fragment_type(ctx, param, value):
    """
    Validate that a given fragment type exists.
    """
    config = ctx.obj.config
    if value and not config.has_fragment_type(value):
        raise click.BadParameter(
            'Missing or unknown fragment type: {}'.format(value))
    return value


def validate_section(ctx, param, value):
    """
    Validate that a given section exists.
    """
    config = ctx.obj.config
    if value and config.has_section(value):
        raise click.BadParameter(
            'Missing or unknown section: {}'.format(value))
    return value


def compose_interactive(
        available_fragment_types: Iterable[str],
        available_sections: Iterable[str],
        **kw):
    """
    Create fragment compose parameters interactively.

    Provided values will act as defaults for their respective prompts.
    """
    fragment_type = prompt_choice(
        'Change type',
        choices=available_fragment_types,
        default=kw.get('fragment_type') or '')
    section = prompt_choice(
        'Section',
        choices=available_sections,
        default=kw.get('section') or '')
    issues = tuple(prompt_many(
        prompt_issue,
        kw.get('issues') or []))
    feature_flags = tuple(prompt_many(
        prompt_feature_flag,
        kw.get('feature_flags', ())))
    description = prompt_markdown(
       'Description',
       default=kw.get('description') or '',
       validator=required).strip()
    change_data = OrderedDict([
        ('fragment_type', fragment_type),
        ('section', section),
        ('issues', issues),
        ('feature_flags', feature_flags),
        ('description', description),
    ])
    kw.update(change_data)
    return kw


def guess_version(ctx, param, value) -> Optional[VersionInfo]:
    """
    Try guess a version.
    """
    if value is not None:
        return (None, value)
    else:
        app = ctx.find_object(Application)
        value = app.guess_version(app.effects.cwd_fs())

    if value is None:
        raise click.BadParameter(
            'Version cannot be guessed, provide it explicitly')
    return parse_version_info(value)
