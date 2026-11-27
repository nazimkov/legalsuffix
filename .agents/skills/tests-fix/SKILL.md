---
name: tests-fix
description: Fix failed MatchingDataTests by delegating each failing data prefix to a sequential subagent.
---

Run all `MatchingDataTests`. For each distinct failing prefix, invoke one `test-fixer` sub-agent scoped to that prefix. Wait for each subagent to finish before starting the next. After all prefixes are handled, rerun all `MatchingDataTests`.

Review each fixer's source evidence and any rows moved to `docs/disputed-test-cases.csv`. Do not discard disputed cases or add unsupported aliases merely to pass tests. Report the results, including each quarantined case, reason, and evidence.
