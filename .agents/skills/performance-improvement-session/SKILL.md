---
name: performance-improvement-session
description: Run a before-and-after performance improvement session.
---

# Performance Improvement Session

Use this skill to improve `src/legalsuffix/matching.py::_find_suffix` and document the measured result in `docs/perf-changelog.md`.

1. Read the current package version from `pyproject.toml` and get the current UTC time. Use `YYYY-MM-DD HH:MM UTC` in a heading of the form `## <date-time> - <current-release>`.
2. Add a new section at the end of `docs/perf-changelog.md`. If the file still has the literal `## <date-time> - <current-release>` template and no dated entries, replace that template with the new heading. Do not edit existing dated sections. Add `### Baseline`, `### Improvement`, `### After`, and `### Difference` subsections; leave `### Improvement` ready for the subagent to fill.
3. Run `uv run python scripts/benchmark-matching.py` from the repository root before changes. Record the exact command and its input, row count, filters, Python/platform, match count, median seconds per pass, throughput, and mean time per call under `### Baseline`. If the benchmark cannot run with its configured input, stop and report the issue rather than changing the benchmark dataset or settings silently.
4. Invoke the `perf-improver` subagent to optimize only `src/legalsuffix/matching.py::_find_suffix`, preserving its behavior. Pass it the exact section heading, baseline results, and the instruction to append its concise techniques-and-effect summary under that heading's `### Improvement`. The subagent must preserve existing baseline notes and report honestly if no safe improvement is found.
5. After the subagent finishes, rerun the same benchmark command with the same input and options. Record the same fields under `### After`. Compare match counts; if they differ, have the subagent investigate and correct the behavioral difference, then rerun the benchmark before completing the report.
6. Under `### Difference`, report the median time change and percent reduction, plus throughput change and percent increase. Calculate time reduction as `(baseline median - after median) / baseline median * 100`; calculate throughput increase as `(after throughput - baseline throughput) / baseline throughput * 100`. Keep negative values when performance regresses, and do not describe a regression as an improvement.
7. Tell the user the session is complete with a short summary of the technique, before/after numbers, and measured difference. Mention if results regressed or no safe optimization was found.

Use identical benchmark settings before and after so the measurements are comparable. Do not change the benchmark script or expand the code scope as part of this session.
