#!/usr/bin/env python3
"""Benchmark ``match_legal_suffix`` against a GLEIF legal-entity-name CSV.

CSV loading and the matcher's first-call suffix-data initialization are kept
outside the timed passes. Each timed pass calls the public matcher once for
every CSV row. Multiple passes help smooth out short-lived system noise.
"""

from __future__ import annotations

import argparse
import csv
import itertools
import platform
import statistics
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_INPUT = ROOT / "tmp" / "20261109-0800-gleif-legal-forms.csv"
NAME_COLUMN = "Entity.LegalName"

# Allow running this script directly from the repository without installing
# the package into the active environment.
sys.path.insert(0, str(ROOT / "src"))

from legalsuffix import match_legal_suffix  # noqa: E402


def _load_names(input_path: Path, limit: int | None) -> list[str]:
    """Read company names before timing so disk and CSV costs are excluded."""
    with input_path.open(encoding="utf-8-sig", newline="") as source:
        reader = csv.DictReader(source)
        if reader.fieldnames is None:
            raise ValueError(f"{input_path}: missing CSV header")
        if NAME_COLUMN not in reader.fieldnames:
            raise ValueError(f"{input_path}: missing CSV column: {NAME_COLUMN}")
        rows = reader if limit is None else itertools.islice(reader, limit)
        return [row[NAME_COLUMN] or "" for row in rows]


def _measure_pass(
    names: list[str],
    country_code: str | None,
    language_code: str | None,
) -> tuple[float, int]:
    """Return elapsed seconds and match count for one complete data pass."""
    matched = 0
    started = time.perf_counter()
    for name in names:
        if match_legal_suffix(name, country_code=country_code, language_code=language_code) is not None:
            matched += 1
    return time.perf_counter() - started, matched


def _format_code(value: str | None) -> str:
    return value if value is not None else "all"


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("input", nargs="?", type=Path, default=DEFAULT_INPUT, help="GLEIF CSV (default: %(default)s)")
    parser.add_argument("--runs", type=int, default=3, help="complete timed passes (default: %(default)s)")
    parser.add_argument(
        "--limit", type=int, default=100_000, help="benchmark only the first N CSV rows (default: all rows)"
    )
    parser.add_argument("--warmup", type=int, default=1_000, help="calls excluded before timing (default: %(default)s)")
    parser.add_argument("--country-code", help="optional country filter passed to match_legal_suffix")
    parser.add_argument("--language-code", help="optional language filter passed to match_legal_suffix")
    args = parser.parse_args()

    if args.runs < 1:
        parser.error("--runs must be at least 1")
    if args.limit is not None and args.limit < 1:
        parser.error("--limit must be at least 1")
    if args.warmup < 0:
        parser.error("--warmup cannot be negative")

    names = _load_names(args.input, args.limit)
    if not names:
        parser.error(f"{args.input}: no company rows found")

    warmup_count = min(args.warmup, len(names))
    for name in names[:warmup_count]:
        match_legal_suffix(name, country_code=args.country_code, language_code=args.language_code)

    elapsed_times: list[float] = []
    match_counts: list[int] = []
    for _ in range(args.runs):
        elapsed, matched = _measure_pass(names, args.country_code, args.language_code)
        elapsed_times.append(elapsed)
        match_counts.append(matched)

    if len(set(match_counts)) != 1:
        raise RuntimeError(f"match count changed between runs: {match_counts}")

    median_seconds = statistics.median(elapsed_times)
    print(f"Input: {args.input}")
    print(f"Company rows: {len(names):,}")
    if args.limit is not None:
        print(f"Row limit: first {args.limit:,} rows")
    print(f"Filters: country={_format_code(args.country_code)}, language={_format_code(args.language_code)}")
    print(f"Warm-up calls (excluded): {warmup_count:,}")
    print(f"Timed passes: {args.runs}")
    print(f"Python: {platform.python_version()} ({platform.python_implementation()})")
    print(f"Platform: {platform.platform()}")
    print(f"Matches per pass: {match_counts[0]:,} ({match_counts[0] / len(names):.2%})")
    print(f"Pass times (seconds): {', '.join(f'{seconds:.3f}' for seconds in elapsed_times)}")
    print(f"Median seconds per pass: {median_seconds:.3f}")
    print(f"Median throughput: {len(names) / median_seconds:,.0f} names/second")
    print(f"Mean seconds per call: {median_seconds / len(names) * 1_000_000:.2f} microseconds")


if __name__ == "__main__":
    main()
