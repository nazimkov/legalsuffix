# Project

Detect, normalize, and strip legal entity suffixes (LLC, LTD, GmbH, OOO, and more) in 20+ languages. Parse company names safely.

# Repository structure

- `src/legalsuffix/` - Python package source.
  - `__init__.py` exposes the package API, update README.md if any changes are made.
  - `matching.py` finds and strips legal suffixes from company names.
  - `loader.py` loads and caches suffix records from the CSV data file.
  - `models.py` defines suffix records, lookup data, and match results.
  - `parser.py` parses and normalizes suffix lists.
  - `validation.py` validates country and language codes.
  - `constants.py` defines paths to package data.
  - `data/suffixes.csv` contains legal entity form records and abbreviations.
- `tests/` - unit tests using the standard-library `unittest` framework.
- `scripts/` - data maintenance scripts.
- `docs/` - reference data and documentation.
- `README.md` - project overview.
- `pyproject.toml` and `uv.lock` - package metadata, development tools, and locked dependencies.

# Workflow

Install dependencies: `uv add <package>`

Run unit tests with: `uv run --directory src python -m unittest discover -s ../tests -t ..`
