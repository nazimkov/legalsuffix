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

## 2026-11-25 12:36 UTC - 0.0.1b6

### Baseline

- Command: `uv run python scripts/benchmark-matching.py`
- Input: `C:\Projects\legalsuffix\tmp\20261109-0800-gleif-legal-forms.csv` (first 100,000 rows)
- Filters: country=all, language=all
- Rows: 100,000
- Warm-up calls (excluded): 1,000; timed passes: 3
- Python: 3.13.5 (CPython)
- Platform: Windows-11-10.0.22631-SP0
- Matches per pass: 79,376 (79.38%)
- Median seconds per pass: 8.777
- Median throughput: 11,394 names/second
- Mean seconds per call: 87.77 microseconds

### Improvement

Replaced temporary string slices used to locate trimmed boundaries with direct
index scans, and skipped redundant candidate trimming when computed boundaries
already guarantee clean spans. The benchmark match count stayed at 79,376.
The suggested trie needs a persistent precomputed index outside
`_find_suffix`, so it did not fit the function-only optimization scope.

### After

- Command: `uv run python scripts/benchmark-matching.py`
- Input: `C:\Projects\legalsuffix\tmp\20261109-0800-gleif-legal-forms.csv` (first 100,000 rows)
- Filters: country=all, language=all
- Rows: 100,000
- Warm-up calls (excluded): 1,000; timed passes: 3
- Python: 3.13.5 (CPython)
- Platform: Windows-11-10.0.22631-SP0
- Matches per pass: 79,376 (79.38%)
- Median seconds per pass: 7.698
- Median throughput: 12,990 names/second
- Mean seconds per call: 76.98 microseconds

### Difference

- Median time: 1.079 seconds lower (12.29% reduction), from 8.777 to 7.698 seconds.
- Median throughput: 1,596 names/second higher (14.01% increase), from 11,394 to 12,990 names/second.

## 2026-11-25 13:24 UTC - 0.0.1b6

### Baseline

- Command: `uv run python scripts/benchmark-matching.py`
- Input: `C:\Projects\legalsuffix\tmp\20261109-0800-gleif-legal-forms.csv` (first 100,000 rows)
- Filters: country=all, language=all
- Rows: 100,000
- Warm-up calls (excluded): 1,000; timed passes: 3
- Python: 3.13.5 (CPython)
- Platform: Windows-11-10.0.22631-SP0
- Matches per pass: 79,376 (79.38%)
- Median seconds per pass: 8.147
- Median throughput: 12,274 names/second
- Mean seconds per call: 81.47 microseconds

### Improvement

Reuse end boundaries for leading and interior candidates, check leading spans
from longest to shortest, and skip Unicode width lookups for ASCII characters.
This reduces boundary and normalization work while preserving match priority.
The suggested tries require a persistent precomputed index outside
`_find_suffix`; building them on each call would add substantial work.

### After

- Command: `uv run python scripts/benchmark-matching.py`
- Input: `C:\Projects\legalsuffix\tmp\20261109-0800-gleif-legal-forms.csv` (first 100,000 rows)
- Filters: country=all, language=all
- Rows: 100,000
- Warm-up calls (excluded): 1,000; timed passes: 3
- Python: 3.13.5 (CPython)
- Platform: Windows-11-10.0.22631-SP0
- Matches per pass: 79,376 (79.38%)
- Median seconds per pass: 7.384
- Median throughput: 13,543 names/second
- Mean seconds per call: 73.84 microseconds

### Difference

- Median time: 0.763 seconds lower (9.37% reduction), from 8.147 to 7.384 seconds.
- Median throughput: 1,269 names/second higher (10.34% increase), from 12,274 to 13,543 names/second.

## 2026-11-25 13:44 UTC - 0.0.1b6

### Baseline

- Command: `uv run python scripts/benchmark-matching.py`
- Input: `C:\Projects\legalsuffix\tmp\20261109-0800-gleif-legal-forms.csv` (first 100,000 rows)
- Filters: country=all, language=all
- Rows: 100,000
- Warm-up calls (excluded): 1,000; timed passes: 3
- Python: 3.13.5 (CPython)
- Platform: Windows-11-10.0.22631-SP0
- Matches per pass: 79,376 (79.38%)
- Median seconds per pass: 5.921
- Median throughput: 16,888 names/second
- Mean seconds per call: 59.21 microseconds

### Improvement

Build forward and reversed tries when suffix data is loaded. For ASCII names
containing words and spaces, walk the tries from both ends and stop when no
longer matching key is possible, avoiding repeated candidate normalization.
Other names retain the existing normalization and candidate lookup path.

### After

- Command: `uv run python scripts/benchmark-matching.py`
- Input: `C:\Projects\legalsuffix\tmp\20261109-0800-gleif-legal-forms.csv` (first 100,000 rows)
- Filters: country=all, language=all
- Rows: 100,000
- Warm-up calls (excluded): 1,000; timed passes: 3
- Python: 3.13.5 (CPython)
- Platform: Windows-11-10.0.22631-SP0
- Matches per pass: 79,376 (79.38%)
- Median seconds per pass: 4.423
- Median throughput: 22,607 names/second
- Mean seconds per call: 44.23 microseconds

### Difference

- Median time: 1.498 seconds lower (25.30% reduction), from 5.921 to 4.423 seconds.
- Median throughput: 5,719 names/second higher (33.86% increase), from 16,888 to 22,607 names/second.
