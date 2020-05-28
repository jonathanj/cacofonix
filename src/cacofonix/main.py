import click
import datetime
from fs import open_fs
from collections import OrderedDict
from typing import Optional, List, Tuple, TextIO

from . import _yaml
from ._app import Application
from ._cli import (
    iso8601date,
    validate_fragment_type,
    validate_section,
    split_issues,
    compose_interactive,
    guess_version)
from ._prompt import (
    print_formatted_yaml_text,
    prompt_confirm)
from ._config import Config
from ._util import (
    pluralize,
    string_escape)
from ._effects import make_effects
from ._log import setup_logging


pass_app = click.make_pass_decorator(Application)


@click.group()
@click.option('--dry-run', '-n', 'dry_run',
              is_flag=True,
              default=False,
              help='''Perform a dry run.''')
@click.option('--log-level',
              default='ERROR',
              type=click.Choice([
                  'DEBUG',
                  'INFO',
                  'WARNING',
                  'ERROR']))
@click.option('--config',
              required=True,
              type=click.File())
@click.version_option()
@click.pass_context
def cli(ctx, config: TextIO, dry_run: bool, log_level: str):
    """
    Compose and compile change fragments into changelogs.

    New changes will be integrated into an existing changelog.
    """
    setup_logging(log_level)
    root_fs = open_fs('.')
    config = Config.parse(config)
    ctx.obj = Application(
        config=config,
        effects=make_effects(root_fs, config, dry_run))
    if dry_run:
        echo_warning('Performing a dry run, no changes will be made!')


@cli.command()
@pass_app
def list_types(app: Application):
    """
    List known fragment types.
    """
    for fragment_type in app.config.available_fragment_types():
        if fragment_type:
            echo_out(fragment_type)


@cli.command()
@pass_app
def list_sections(app: Application):
    """
    List known sections.
    """
    for section in app.config.available_sections():
        if section:
            echo_out(section)


@cli.command()
@pass_app
def list_versions(app: Application):
    """
    List all versions tracked by this tool.
    """
    for version in app.known_versions():
        echo = echo_warning_out if version.prerelease else echo_out
        echo(str(version))


@cli.command()
@click.option('-t', '--type', 'fragment_type',
              callback=validate_fragment_type,
              help='Fragment type, should match a value from `list-types`')
@click.option('-s', '--section',
              callback=validate_section,
              help='Section type, should match a value from `list-sections`')
@click.option('-i', '--issue', 'issues',
              multiple=True,
              callback=split_issues,
              help='''Related issue, should be formatted as issue_number or
              issue_number:issue_url, can be specified multiple times''')
@click.option('-f', '--feature-flag', 'feature_flags',
              multiple=True,
              help='Required feature flag, can be specified multiple times')
@click.option('-d', '--description',
              help='Description of the change')
@click.option('--edit',
              is_flag=True,
              default=None,
              help='Complete the changelog fragment in EDITOR')
@click.option('--interactive / --no-interactive',
              is_flag=True,
              help='Complete the changelog fragment interactively')
@pass_app
def compose(app: Application, interactive: bool, **kw):
    """
    Compose a new change fragment.

    Preset values can be given as options with the unspecified value being
    completed interactively or via a text editor.
    """
    def _validate(yaml_text):
        try:
            app.validate_fragment_text(yaml_text)
            return True
        except Exception as e:
            echo_error('Oops! There was a problem with your change data.')
            echo(str(e))
            return False

    def _compose(fragment_type: str,
                 section: Optional[str],
                 issues: List[Tuple[str, str]],
                 feature_flags: List[str],
                 description: str,
                 edit: bool):
        change_fragment_data = OrderedDict([
            ('type', fragment_type),
            ('section', section),
            ('issues', dict(issues)),
            ('feature_flags', list(feature_flags)),
            ('description', _yaml.literal_str(
                string_escape(description or ''))),
        ])
        yaml_text = _yaml.dump(change_fragment_data)

        echo_info('\nOkay, this is your change:\n')
        print_formatted_yaml_text(yaml_text)

        edit = kw.get('edit')
        if interactive:
            if edit is None:
                edit = prompt_confirm('Open it in your editor?')
        else:
            if not _validate(yaml_text):
                raise SystemExit(2)

        if edit:
            while True:
                yaml_text = click.edit(
                    yaml_text,
                    require_save=False,
                    extension='.yaml')
                if not yaml_text:
                    echo_error('Aborting composition!')
                    raise SystemExit(2)

                if _validate(yaml_text):
                    break
                else:
                    if not prompt_confirm('Open it in your editor?'):
                        raise SystemExit(2)
                    else:
                        continue

        fragment_filename = app.create_new_fragment(yaml_text)
        echo_success('Wrote new fragment {}'.format(fragment_filename))

    if interactive:
        config = app.config
        kw = compose_interactive(
            available_sections=config.available_sections(),
            available_fragment_types=config.available_fragment_types(),
            **kw)
    return _compose(**kw)


@cli.command()
@click.option('--draft',
              is_flag=True,
              help='Do not perform any permanent actions.')
@click.option('--version', 'project_version',
              default=None,
              callback=guess_version,
              help='Version to stamp in the changelog.')
@click.option('--date', 'version_date',
              callback=iso8601date,
              help='ISO8601 date for the changelog, defaults to today.')
@click.option('--archive / --no-archive', 'archive_fragments',
              is_flag=True,
              default=None,
              help='Archive fragments after writing a new changelog.')
@click.option('--confirm / --no-confirm', 'confirm_write',
              is_flag=True,
              default=True,
              help='Confirm before writing the changelog')
@pass_app
def compile(app: Application,
            draft: bool,
            project_version: Tuple[Optional[str], str],
            version_date: datetime.date,
            archive_fragments: Optional[bool],
            confirm_write: bool):
    """
    Compile change fragments into a changelog.

    The existing changelog will be updated with the new changes, and the old
    change fragments discarded.
    """
    version_guess, version_number = project_version
    if version_guess is not None:
        echo('Guessed version {} via {}'.format(
            version_number, version_guess))

    new_fragments = list(app.find_new_fragments())

    with open_fs('temp://') as tmp_fs:
        n = len(app.compile_fragment_files(tmp_fs, new_fragments))
        echo('Found {} new changelog fragments'.format(n))
        changelog = app.render_changelog(
            fs=tmp_fs,
            version=version_number,
            version_date=version_date)

    if draft:
        echo_info(
            'Showing a draft changelog -- no changes will be made!\n')
        echo_out(changelog)
        return

    echo_info('This is the changelog to be added:\n')
    echo_out(changelog)
    if confirm_write:
        if not prompt_confirm('Merge this with the existing changelog?'):
            echo_info('Aborting at user request')
            raise SystemExit(2)

    app.merge_with_existing_changelog(changelog)
    echo_success('Wrote changelog.')

    if n:
        if archive_fragments is None:
            archive_fragments = prompt_confirm(
                'Archive {} {}?'.format(
                    n, pluralize(n, 'fragment', 'fragments')),
                default=True)
        if archive_fragments:
            n, not_removed = app.archive_fragments(
                found_fragments=new_fragments,
                version=version_number,
                version_date=version_date,
                version_author=app.effects.git_user())
            if not_removed:
                echo_error('Could not archive the following:')
                for name in not_removed:
                    echo(name)
            else:
                echo_info(
                    'Archived {} {} as version {}.'.format(
                        n,
                        pluralize(n, 'fragment', 'fragments'),
                        version_number))


def echo_partial(**kw):
    """
    Partially applied version of `click.secho`.
    """
    return lambda msg: click.secho(msg, **kw)


echo = echo_partial(err=True)
echo_out = echo_partial()
echo_error = echo_partial(fg='red', err=True)
echo_info = echo_partial(fg='yellow', err=True)
echo_warning = echo_partial(fg='bright_yellow', err=True)
echo_warning_out = echo_partial(fg='bright_yellow')
echo_success = echo_partial(fg='green', err=True)


def main():
    cli()


if __name__ == '__main__':
    main()
