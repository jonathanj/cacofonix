import click
import os
import secrets
import time
from aniso8601 import parse_date
from collections import OrderedDict
from datetime import date


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


def validate_or_generate_output_path(ctx, param, output_path):
    """
    Valid or generate the output path for composing a fragment.
    """
    config = ctx.obj.config
    if output_path is None:
        filename = '{}-{}.yaml'.format(
            int(time.time() * 1000),
            secrets.token_urlsafe(6))
        output_path = os.path.join(config.change_fragments_path, filename)
    if os.path.exists(output_path):
        raise click.BadParameter(
            'File already exists, refusing to overwrite {}'.format(
                output_path))
    return output_path


def compose_interactive(available_fragment_types, available_sections, **kw):
    """
    Create fragment compose parameters interactively.

    Provided values will act as defaults for their respective prompts.
    """
    fragment_type = click.prompt(
        'Change type',
        default=kw.get('fragment_type'),
        type=click.Choice(available_fragment_types))
    section = click.prompt(
        'Section (press ENTER for default)',
        default=kw.get('section') or '',
        type=click.Choice(available_sections))
    issues = kw.get('issues') or []
    # Prompt for multiple issue numbers and URLs.
    while True:
        issue = click.prompt(
            '{} number (press ENTER to skip)'.format(
                'Another issue' if issues else 'Issue'),
            default='',
            type=str).strip()
        issue_url = None
        if issue:
            while not issue_url:
                issue_url = click.prompt(
                    'URL for issue {}'.format(issue),
                    default='',
                    type=str).strip()
            issues.append((issue, issue_url))
        else:
            break

    # Prompt for multiple feature flags.
    feature_flags = kw.get('feature_flags') or ()
    while True:
        feature_flag = click.prompt(
            '{} flag (press ENTER to skip)'.format(
                'Another feature' if feature_flags else 'Feature'),
            default='',
            type=str).strip()
        if feature_flag:
            feature_flags += (feature_flag,)
        else:
            break

    description = click.prompt(
        'Description',
        default=kw.get('description'),
        type=str).strip()

    edit = kw.get('edit')
    if edit is None:
        edit = click.confirm('Edit saved fragment?')

    change_data = OrderedDict([
        ('fragment_type', fragment_type),
        ('section', section),
        ('issues', issues),
        ('feature_flags', feature_flags),
        ('description', description),
        ('edit', edit),
    ])
    kw.update(change_data)
    return kw
