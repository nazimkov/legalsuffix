#!/usr/bin/env python3
"""Convert suffix_details.json to suffixes.tsv.

TSV format:  <ISO>\t<suffix1>|<suffix2>|...

- Input JSON is a list of objects:
    { "suffix": str, "full_name": str, "variants": [str], "countries": [str] }
- Every variant (and the canonical suffix itself) is normalized and
  attributed to every country in "countries".
- Output is sorted by ISO code, then by suffix (longest first) so that
  longest-match-first consumers work out of the box.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from collections import defaultdict
from pathlib import Path

# Internal dots collapse only when between word chars: "s.a." -> "sa", "e.v." -> "ev"
_INTERNAL_DOTS = re.compile(r"(?<=\w)\.(?=\w)")


def norm(s: str) -> str:
    """Normalize a suffix for matching: lowercase, strip outer punctuation,
    collapse internal dots, collapse whitespace."""
    s = s.strip().lower()
    s = s.strip("()[]{}\"'")
    s = _INTERNAL_DOTS.sub("", s)  # "s.a." -> "sa", "e.v." -> "ev"
    s = s.rstrip(".,;")  # trailing "ltd." -> "ltd"
    s = re.sub(r"\s+", " ", s)  # "pte  ltd" -> "pte ltd"
    return s.strip()


def build_index(records: list[dict]) -> dict[str, set[str]]:
    """Return {iso: {normalized_suffix, ...}}.

    Adds both the canonical suffix and every variant. Unknown/malformed
    records raise with context so bad data doesn't slip through silently.
    """
    index: dict[str, set[str]] = defaultdict(set)
    for i, rec in enumerate(records):
        if not isinstance(rec, dict):
            raise ValueError(f"record #{i}: expected object, got {type(rec).__name__}")
        suffix = rec.get("suffix")
        countries = rec.get("countries")
        variants = rec.get("variants") or []
        if not isinstance(suffix, str) or not suffix.strip():
            raise ValueError(f"record #{i}: missing/empty 'suffix'")
        if not isinstance(countries, list) or not countries:
            raise ValueError(f"record #{i}: missing/empty 'countries'")
        if not isinstance(variants, list):
            raise ValueError(f"record #{i}: 'variants' must be a list")

        forms = {norm(suffix)} | {norm(v) for v in variants}
        forms.discard("")

        for iso in countries:
            iso = str(iso).strip().upper()
            if len(iso) != 2 or not iso.isalpha():
                raise ValueError(f"record #{i}: bad ISO code {iso!r}")
            index[iso].update(forms)
    return index


def render_tsv(index: dict[str, set[str]], header_comment: str | None = None) -> str:
    """Render the TSV. Suffixes per country sorted longest-first, then alpha."""
    lines: list[str] = []
    if header_comment:
        for line in header_comment.splitlines():
            lines.append(f"# {line}".rstrip())
    for iso in sorted(index):
        sfs = sorted(index[iso], key=lambda s: (-len(s), s))
        lines.append(f"{iso}\t{'|'.join(sfs)}")
    return "\n".join(lines) + "\n"


def convert(json_path: Path, tsv_path: Path, header_comment: str | None = None) -> None:
    records = json.loads(json_path.read_text(encoding="utf-8"))
    if not isinstance(records, list):
        raise ValueError(f"{json_path}: top-level JSON must be a list")
    index = build_index(records)
    tsv_path.write_text(render_tsv(index, header_comment), encoding="utf-8")
    total_suffixes = sum(len(v) for v in index.values())
    print(
        f"wrote {tsv_path}  ({len(index)} countries, {total_suffixes} suffix entries)",
        file=sys.stderr,
    )


def main() -> None:
    description = __doc__.splitlines()[0] if __doc__ else "Convert suffix_details.json to suffixes.tsv"
    ap = argparse.ArgumentParser(description=description)
    ap.add_argument("input", nargs="?", default="suffix_details.json", type=Path)
    ap.add_argument("output", nargs="?", default="suffixes.tsv", type=Path)
    ap.add_argument("--no-comment", action="store_true", help="omit header comment")
    args = ap.parse_args()

    header = (
        None
        if args.no_comment
        else (
            "Generated from suffix_details.json by convert.py\n"
            "Format: ISO<TAB>suffix1|suffix2|...  (sorted longest-first)"
        )
    )
    convert(args.input, args.output, header)


if __name__ == "__main__":
    main()
