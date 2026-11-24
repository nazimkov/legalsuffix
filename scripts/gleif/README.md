# GLEIF scripts

Run these commands from the repository root. Install the project dependencies with `uv sync` first.

## Extract legal form records

```powershell
uv run python scripts/gleif/extract-legal-forms.py tmp/gleif.csv tmp/legal-forms.csv
```

Reads a GLEIF CSV and writes LEI, entity name, legal form code, and country for rows with a legal form code. If paths are omitted, it uses the dated input and output files under `tmp/` defined in the script.

## Sample test cases

```powershell
uv run python scripts/gleif/sample-test-cases.py tmp/legal-forms.csv tmp/test-data/sampled-test-cases.csv --countries 20 --codes-per-country 3 --seed 42
```

Selects a reproducible sample from common country and ELF-code combinations, skipping LEIs already in `tests/data/` or the uncertain-cases file. Defaults to 20 countries and 3 codes per country; the input and output paths also have defaults.

## Extract suffixes with the LLM

Copy `scripts/gleif/example.env` to `scripts/gleif/.env` and fill in the Azure OpenAI and OpenRouter settings. Then run:

```powershell
uv run python -m scripts.gleif.extract-llm tmp/test-data/sampled-test-cases.csv
```

Extracts and validates company names in batches of 10, saving timestamped JSON batch files under `tmp/test-data/extracted-llm/`. Add `--test-run` to process only the first 20 rows. The input defaults to `tmp/test-data/sampled-test-cases.csv`.

## Combine and classify results

```powershell
uv run python -m scripts.gleif.combine-llm
```

Combines a run's JSON batches into review and final CSV files. By default it uses the newest run; pass its timestamped directory to select another, for example:

```powershell
uv run python -m scripts.gleif.combine-llm tmp/test-data/extracted-llm/20261123-120000-000000
```

It also updates categorized CSVs in `tests/data/` and records uncertain results in `tmp/test-data/uncertain-cases.csv`. Use `--input`, `--test-cases-root`, or `--uncertain-cases` to change those paths.
