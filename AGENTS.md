# Project

Detect, normalize, and strip legal entity suffixes (LLC, LTD, GmbH, OOO, and more) in 20+ languages. Parse company names safely.

# Repository structure

- `src/legalsuffix/` - Python package source.
  - `parser.py` parses and normalizes the suffix TSV data.
  - `matching.py` finds and strips legal suffixes from company names.
  - `loader.py` loads and caches the suffix data.
  - `models.py` defines the suffix lookup data model.
  - `countries.py` validates country codes and support.
  - `constants.py` defines paths to package data.
  - `data/suffixes.tsv` contains country-specific suffixes.
- `tests/` - unit tests, using the standard-library `unittest` framework.
- `scripts/` - maintenance and conversion scripts for suffix data.
- `docs/` - generated or reference documentation about suffixes.
- `README.md` - project overview.
- `pyproject.toml` and `uv.lock` - package metadata, development tools, and locked dependencies.

# Workflow

Install dependencies: `uv add <package>`

Run unit tests with: `uv run --directory src python -m unittest discover -s ../tests`
