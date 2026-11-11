# Performance Changes

## 2026-11-11 10:31 UTC - 0.0.1b5

### Baseline

- Command: `uv run python scripts/benchmark-matching.py`
- Input: `C:\Projects\legalsuffix\tmp\20261109-0800-gleif-legal-forms.csv` (first 100,000 rows)
- Filters: country=all, language=all
- Rows: 100,000
- Warm-up calls (excluded): 1,000; timed passes: 3
- Python: 3.13.5 (CPython)
- Platform: Windows-11-10.0.22631-SP0
- Matches per pass: 77,996 (78.00%)
- Median seconds per pass: 14.965
- Median throughput: 6,682 names/second
- Mean seconds per call: 149.65 microseconds

### Improvement

Check trailing candidates in match-priority order and return the first match.
For interior matches, calculate end boundaries once and skip candidates shorter
than the best match. This avoids unnecessary normalization and match creation.

### After

- Command: `uv run python scripts/benchmark-matching.py`
- Input: `C:\Projects\legalsuffix\tmp\20261109-0800-gleif-legal-forms.csv` (first 100,000 rows)
- Filters: country=all, language=all
- Rows: 100,000
- Warm-up calls (excluded): 1,000; timed passes: 3
- Python: 3.13.5 (CPython)
- Platform: Windows-11-10.0.22631-SP0
- Matches per pass: 77,996 (78.00%)
- Median seconds per pass: 5.533
- Median throughput: 18,075 names/second
- Mean seconds per call: 55.33 microseconds

### Difference

- Median time: 9.432 seconds lower (63.03% reduction), from 14.965 to 5.533 seconds.
- Median throughput: 11,393 names/second higher (170.50% increase), from 6,682 to 18,075 names/second.
