from prompt_toolkit import (
    print_formatted_text,
    prompt as _prompt)
from prompt_toolkit.completion import WordCompleter
from prompt_toolkit.formatted_text import PygmentsTokens
from prompt_toolkit.key_binding import KeyBindings
from prompt_toolkit.lexers import PygmentsLexer
from prompt_toolkit.styles import Style
from prompt_toolkit.styles import style_from_pygments_cls, merge_styles
from prompt_toolkit.validation import Validator
from pygments import lex
from pygments.styles import get_style_by_name
from pygments.lexers.data import YamlLexer
from pygments.lexers.markup import MarkdownLexer
from typing import Any, Callable, Iterable, List, Optional, Tuple, Union


default_style = style_from_pygments_cls(get_style_by_name('monokai'))
prompt_style = merge_styles([
    default_style,
    Style.from_dict({
        'prompt': 'cyan',
        'hint': 'grey',
    })
])


PromptTextList = List[Tuple[str, str]]
PromptMessage = Union[str, PromptTextList]
PromptManyResults = Iterable[Any]
PromptFunc = Callable[[PromptManyResults], str]


def prompt(
        message: PromptMessage,
        hint: Optional[str] = None,
        *a,
        multiline=False,
        **kw):
    """
    Wrapper around ``prompt_toolkit.prompt``.
    """
    if isinstance(message, str):
        message = [('class:prompt', f'{message}')]
    if hint is not None:
        message = message + [('class:hint', f' ({hint})')]
    message = message + [('class:prompt', ': ')]
    if multiline:
        message = message + [('class:prompt', '\n')]
    return _prompt(
        message, *a,
        style=prompt_style,
        multiline=multiline,
        include_default_pygments_style=False,
        **kw)


def validator(error_message: str):
    """
    Decorate a predicate function as a ``prompt_toolkit`` validator.
    """
    def _validation(f):
        return Validator.from_callable(
            f,
            error_message=error_message,
            move_cursor_to_end=True)
    return _validation


def is_one_of(words: List[str]):
    """
    Value exists in some set.
    """
    error_message = 'Value must be one of: {}'.format(
        ', '.join(words))
    return validator(error_message)(lambda word: word in words)


@validator('Value is required')
def required(value: Any):
    """
    Value is required.
    """
    return bool(value)


def prompt_choice(prompt_text: str, choices: Iterable[str], default: str = ''):
    """
    Prompt for a single choices from a set of options.
    """
    completer = WordCompleter(choices)
    choices_text = ', '.join(choices)
    return prompt(
        prompt_text,
        hint=choices_text,
        default=default,
        completer=completer,
        validator=is_one_of(choices))


def prompt_many(
        prompt_func: PromptFunc,
        initial: PromptManyResults = []) -> PromptManyResults:
    """
    Prompt for many of the same thing.

    Prompting ends when ``prompt_func`` returns ``None``.
    """
    results = list(initial)
    while True:
        result = prompt_func(results)
        if not result:
            break
        results.append(result)
    return results


def prompt_feature_flag(results: PromptManyResults = []) -> Optional[str]:
    """
    Prompt for a feature flag name.
    """
    return prompt(
        '{} flag'.format('Another feature' if results else 'Feature'),
        hint='ENTER to skip'
    ).strip()


def prompt_issue(results: PromptManyResults = []) -> Optional[Tuple[str, str]]:
    """
    Prompt for an issue and issue URL.
    """
    issue = prompt(
        '{} number'.format('Another issue' if results else 'Issue'),
        hint='ENTER to skip'
    ).strip()
    if issue:
        issue_url = prompt(
            'Issue URL',
            hint=f'for issue {issue}',
            validator=required).strip()
        return (issue, issue_url)
    return None


def prompt_markdown(message: PromptMessage, **kw) -> str:
    """
    Prompt for a multiline Markdown input.
    """
    kb = KeyBindings()

    @kb.add('c-d')
    def _(event):
        event.current_buffer.validate_and_handle()
    return prompt(
        message,
        hint='Ctrl-D to finish',
        multiline=True,
        key_bindings=kb,
        lexer=PygmentsLexer(MarkdownLexer),
        **kw)


def prompt_confirm(message: PromptMessage, default=False, **kw) -> bool:
    """
    Prompt for a yes/no response.
    """
    kb = KeyBindings()

    @kb.add('y', eager=True)
    @kb.add('n', eager=True)
    def one_key(event):
        event.current_buffer.insert_text(event.key_sequence[0].key)
        event.current_buffer.validate_and_handle()

    @kb.add('enter', eager=True)
    def _(event):
        event.current_buffer.insert_text('y' if default else 'n')
        event.current_buffer.validate_and_handle()

    @kb.add('<any>', eager=False)
    def _(event):
        pass

    return prompt(
        message,
        hint='Y/n' if default else 'y/N',
        key_bindings=kb,
        **kw).lower() == 'y'


def print_formatted_yaml_text(yaml_text: str) -> None:
    """
    """
    tokens = list(lex(yaml_text, lexer=YamlLexer()))
    print_formatted_text(PygmentsTokens(tokens), style=prompt_style)
