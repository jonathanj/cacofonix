import click
import datetime
from collections import OrderedDict
from typing import Optional, List, Tuple, TextIO

from . import _yaml
from ._app import Application
from ._cli import (
    iso8601date,
    validate_or_generate_output_path,
    validate_fragment_type,
    validate_section,
    split_issues,
    compose_interactive,
    guess_version)
from ._config import Config
from ._util import (
    TemporaryDirectory,
    git_stage,
    pluralize,
    string_escape,
    ensure_dir_exists)


pass_app = click.make_pass_decorator(Application)


@click.group()
@click.option('--config',
              required=True,
              type=click.File())
@click.version_option()
@click.pass_context
def cli(ctx, config: TextIO):
    """
    Compose and compile change fragments into changelogs.

    New changes will be integrated into an existing changelog.
    """
    ctx.obj = Application(Config.parse(config))


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
@click.option('-o', '--output', 'output_path',
              type=click.Path(writable=True, dir_okay=False),
              callback=validate_or_generate_output_path,
              help='Path to write the fragment to')
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
    def _compose(fragment_type: str,
                 section: Optional[str],
                 issues: List[Tuple[str, str]],
                 feature_flags: List[str],
                 description: str,
                 output_path: str,
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
        if edit:
            yaml_text = click.edit(
                yaml_text,
                require_save=False,
                extension='.yaml')
            if not yaml_text:
                echo_error('Aborting composition!')
                raise SystemExit(2)
            # TODO: Validate `yaml_text`

        with open(ensure_dir_exists(output_path), 'w') as fd:
            fd.write(yaml_text)
        echo_success('Wrote fragment {}'.format(output_path))
        git_stage(output_path)

    config = app.config
    kw = kw if not interactive else compose_interactive(
        available_sections=config.available_sections(),
        available_fragment_types=config.available_fragment_types(),
        **kw)
    return _compose(**kw)


@cli.command()
@click.option('--draft',
              is_flag=True,
              help='Do not perform any permanent actions.')
@click.option('--version', 'project_version',
              type=str,
              default=None,
              callback=guess_version,
              help='Version for the changelog.')
@click.option('--date', 'project_date',
              callback=iso8601date,
              help='ISO8601 date for the changelog, defaults to today.')
@click.option('--delete / --no-delete', 'remove_fragments',
              is_flag=True,
              default=None,
              help='Delete old changelog fragments.')
@pass_app
def compile(app: Application,
            draft: bool,
            project_version: Tuple[Optional[str], str],
            project_date: datetime.date,
            remove_fragments: Optional[bool]):
    """
    Compile change fragments into a changelog.

    The existing changelog will be updated with the new changes, and the old
    change fragments discarded.
    """
    changelog_path = app.config.changelog_path
    with TemporaryDirectory() as parent_dir:
        version_guess, version_number = project_version
        if version_guess is not None:
            echo('Guessed version {} via {}'.format(
                version_number, version_guess))
        fragment_paths = list(app.find_all_fragments())
        n = app.compile_fragment_files(parent_dir, fragment_paths)
        echo('Found {} changelog fragments'.format(n))
        changelog = app.render_changelog(
            parent_dir=parent_dir,
            project_version=version_number,
            project_date=project_date.isoformat())
        if draft:
            echo_warning(
                'Showing a draft changelog -- no actions will be performed!\n')
            echo_out(changelog)
            return

        app.merge_with_existing_changelog(changelog)
        echo_success('Wrote changelog {}'.format(changelog_path))
        git_stage(changelog_path)
        echo_success('Staged {} in git'.format(changelog_path))
        if n:
            if remove_fragments is None:
                remove_fragments = click.confirm(
                    'Remove {} {}?'.format(
                        n, pluralize(n, 'fragment', 'fragments')),
                    default=True)
            if remove_fragments:
                n, not_removed = app.remove_fragments()
                if not_removed:
                    echo_error('Could not remove the following:')
                    for name in not_removed:
                        echo(name)
                else:
                    echo_warning(
                        'Removed {} old {}.'.format(
                            n,
                            pluralize(n, 'fragment', 'fragments')))


def echo_partial(**kw):
    """
    Partially applied version of `click.secho`.
    """
    return lambda msg: click.secho(msg, **kw)


echo = echo_partial(err=True)
echo_out = echo_partial()
echo_error = echo_partial(fg='red', err=True)
echo_warning = echo_partial(fg='yellow', err=True)
echo_success = echo_partial(fg='green', err=True)


def main():
    cli()


if __name__ == '__main__':
    main()
