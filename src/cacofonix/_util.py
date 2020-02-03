from codecs import encode, decode


def pluralize(n: int, singular: str, plural: str) -> str:
    """
    Use the plural or singular form based on some count.
    """
    return singular if n == 1 else plural


def string_escape(s: str) -> str:
    """
    Like `.decode('string-escape')` in Python 2 but harder because Python 3.
    """
    return decode(encode(s, 'latin-1', 'backslashreplace'), 'unicode-escape')
