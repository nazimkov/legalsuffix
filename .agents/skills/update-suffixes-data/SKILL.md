---
name: update-suffixes-data
description: Maintain the ELF code list and refresh the package suffix data when its source changes.
---

# Update Suffixes Data

Use this skill when changing the ELF source list or refreshing its packaged copy. The maintained source is `docs/2026-02-19-elf-code-list-v1.6.csv`; the package data is `src/legalsuffix/data/suffixes.csv`.

## Update the source list

Use reliable sources to verify legal-form names, abbreviations, language, and country applicability. Preserve the source CSV's columns and formatting. Abbreviations are semicolon-separated in `Abbreviations Local language` and `Abbreviations transliterated`; country association is recorded in `Country Code (ISO 3166-1)`. Keep country codes valid and uppercase. Do not infer applicability from a similar legal system.

## Refresh the packaged copy

Run the importer only when the source CSV has changed or the packaged copy needs to be refreshed. From the repository root, run:

```powershell
uv run python scripts/import-elf-codes.py
```

The importer overwrites `src/legalsuffix/data/suffixes.csv`, removes administrative columns, and excludes ELF codes `8888` and `9999`.

Review the source and package data diffs. Confirm the requested records and abbreviations appear, reserved codes `8888` and `9999` are absent from the package file, and unrelated records remain. Do not run the importer when no source or packaged data update is needed.
