from functools import lru_cache

from .constants import DATA_FILE_PATH
from .models import LegalSuffixes
from .parser import parse_suffixes


@lru_cache(maxsize=1)
def load_suffixes() -> LegalSuffixes:
    content = DATA_FILE_PATH.read_text(encoding="utf-8")
    return parse_suffixes(content)
