"""Public API for detecting and working with legal suffixes.

Example:
    >>> from legalsuffix import parse_company_name
    >>> parsed = parse_company_name("Acme GmbH", country_code="DE")
    >>> parsed.name
    'Acme'
    >>> parsed.suffix.suffix
    'GmbH'
"""

from .loader import list_legal_suffixes
from .matching import match_legal_suffix, normalize_legal_suffix, parse_company_name, strip_legal_suffix
from .models import LegalSuffix, LegalSuffixMatch, ParsedCompanyName

__version__ = "0.0.1b6"

__all__ = [
    "LegalSuffix",
    "LegalSuffixMatch",
    "ParsedCompanyName",
    "list_legal_suffixes",
    "match_legal_suffix",
    "normalize_legal_suffix",
    "parse_company_name",
    "strip_legal_suffix",
]
