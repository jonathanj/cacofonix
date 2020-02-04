from typing import Any, Dict, Tuple, Callable, Optional
from fs.base import FS


# TODO: Python 3.7 doesn't have `TypedDict`.
Fragment = Dict[str, Any]
# TODO: Python 3.7 doesn't have `Literal`.
# OutputType = Literal['markdown', 'rest']
OutputType = str
FoundFragment = Tuple[FS, str]
GuessPair = Tuple[str, Callable[[FS], Optional[str]]]
