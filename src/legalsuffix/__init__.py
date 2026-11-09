"""Public API for detecting and working with legal suffixes.

Example:
    >>> from legalsuffix import parse_company_name
    >>> parsed = parse_company_name("Acme GmbH", country_code="DE")
    >>> parsed.name
    'Acme'
    >>> parsed.suffix.suffix
    'GmbH'
"""

from .loader import get_suffixes
from .matching import match_legal_suffix, normalize_legal_suffix, parse_company_name, strip_legal_suffix
from .models import LegalSuffix, LegalSuffixMatch, ParsedCompanyName

__version__ = "0.1.0"

__all__ = [
    "LegalSuffix",
    "LegalSuffixMatch",
    "ParsedCompanyName",
    "get_suffixes",
    "match_legal_suffix",
    "normalize_legal_suffix",
    "parse_company_name",
    "strip_legal_suffix",
]
