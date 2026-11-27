---
name: update-suffixes-data
description: Maintain the ELF code list and refresh the package suffix data when its source changes.
---

# Update Suffixes Data

Use this skill when changing the ELF source list or refreshing its packaged copy. The local source is `tmp/2026-02-19-elf-code-list-v1.6.csv`; the package data is `src/legalsuffix/data/suffixes.csv`.

See `docs/extra-elf-codes.csv` for curated additions. `EXTRA_SUFFIX` merges abbreviations into an official record identified by ELF code, country, and language. `NEW` appends a complete record, including one absent from the official list; use `8888` for a new form without a specific ELF code.

## Update the source list

Use reliable sources to verify legal-form names, abbreviations, language, and country applicability. Preserve the source CSV's columns and formatting. Abbreviations are semicolon-separated in `Abbreviations Local language` and `Abbreviations transliterated`; country association is recorded in `Country Code (ISO 3166-1)`. Keep country codes valid and uppercase. Do not infer applicability from a similar legal system.

## Refresh the packaged copy

Run the importer only when the source CSV has changed or the packaged copy needs to be refreshed. From the repository root, run:

```powershell
uv run python scripts/gleif/import-elf.py
```

The importer overwrites `src/legalsuffix/data/suffixes.csv`, removes administrative columns, and excludes official source rows with ELF codes `8888` and `9999`. It retains explicitly curated `NEW` records, including those using reserved codes.

Review the source and package data diffs. Confirm requested records and abbreviations appear, any reserved-code package rows come from curated `NEW` records, and unrelated records remain. Do not run the importer when no source or packaged data update is needed.
