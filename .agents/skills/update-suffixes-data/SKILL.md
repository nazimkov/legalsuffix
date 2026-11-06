---
name: update-suffixes-data
description: Update legal entity suffix records in docs/suffix_details.json and regenerate the package suffix data when a user asks to add, change, or remove suffixes.
---

# Update Suffixes Data

Use this skill for requests to maintain the legal suffix dataset. The human-readable source is `docs/suffix_details.json`; the generated runtime data is `src/legalsuffix/data/suffixes.tsv`.

## Record format

The JSON top level is an array. Each record has these fields:

```json
{
  "suffix": "srl",
  "full_name": "Sociedad de Responsabilidad Limitada",
  "variants": ["s.r.l.", "srl"],
  "countries": ["AR", "PE"]
}
```

- `suffix`: canonical short form. This is included as a match form alongside all `variants`.
- `full_name`: expanded legal form for readers. Keep it present and accurate; the generator currently does not use it in the TSV.
- `variants`: alternative written forms, including commonly used punctuation or spacing differences. The generator lowercases forms, strips outer brackets/quotes and trailing punctuation, removes dots between word characters, and collapses whitespace, so list meaningful forms rather than redundant capitalization-only variants.
- `countries`: ISO 3166-1 alpha-2 codes where the canonical form and every listed variant should match. The generator applies every form in the record to every country in this list. Use uppercase codes and verify they are valid; do not include countries based only on a similar legal system or an unverified assumption.

Keep valid JSON, preserve Unicode characters, and follow the existing readable indentation and ordering. When facts about a legal form, official name, or country applicability are uncertain, check a reliable source before editing rather than guessing.

## Regenerate the runtime data

After changing the JSON, run from the repository root:

```powershell
uv run python scripts/update-data.py docs/suffix_details.json src/legalsuffix/data/suffixes.tsv
```

This command overwrites the TSV. The updater validates the top-level array and required suffix, variants, and country values, normalizes the match forms, merges duplicates per country, and sorts countries and suffixes (longest first). It does not validate `full_name` or verify that a two-letter country code is a real ISO code, so review those fields yourself.

Review the diff for both files after regeneration. Confirm each new or changed form appears under the intended country codes and that unrelated suffix entries were not lost. Do not edit the generated TSV by hand; correct the JSON source and regenerate it instead.
