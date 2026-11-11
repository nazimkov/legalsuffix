# Development

## Prerequisites

Install Python 3.12 or later and [uv](https://docs.astral.sh/uv/getting-started/installation/).

To install uv, use the command for your platform:

**Windows (PowerShell):**

```powershell
powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"
```

**macOS and Linux:**

```shell
curl -LsSf https://astral.sh/uv/install.sh | sh
```

## Set up the project

From the repository root, sync the project and its development dependencies:

```shell
uv sync
```

Install the pre-commit hook:

```shell
uv run pre-commit install
```

The hook runs the unit tests and refreshes the coverage badge before a commit
that changes a Python file under `src/`. If the badge changes, stage `README.md`
and retry the commit so the updated coverage is included.

## Run tests

From the repository root, run the unit test suite with:

```shell
uv run --directory src python -m unittest discover -s ../tests -t ..
```
