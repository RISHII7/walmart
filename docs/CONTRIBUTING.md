# Contributing

## Branch naming

| Prefix | Use for |
|---|---|
| `feature/<name>` | New functionality — a new model, a new layer, a new integration |
| `fix/<name>` | Correcting a bug or misconfiguration |
| `test/<name>` | Adding test coverage without changing behavior |

## Commit messages

Write the *why*, not just the *what* — the diff already shows what changed. A good
commit message here explains the reasoning: what problem existed, why this approach
fixes it, and what tradeoff (if any) was made. See the project's own git history for
the standard this aims for.

## Before opening a pull request

- **Check for secrets.** Anything sensitive (connection strings, tokens, generated
  config files carrying keys) must never be staged. `.gitignore` already excludes the
  known patterns (`.env`, `connection.txt`, `profiles.yml`, `airflow.cfg`, `logs/`) —
  when adding a new kind of local-only file, add its pattern before committing
  anything that touches it, not after.
- **Verify the change actually works**, not just that it compiles/parses. For a dbt
  model: `dbt run`/`dbt test` against a real target. For a DAG change: at minimum
  `dbt parse`/`airflow dags list-import-errors`; ideally a real DAG run.
- **Keep the diff scoped** to the stated purpose of the branch — a fix branch fixes
  one thing, a feature branch adds one thing.

## Pull requests

- Base: `main`.
- Body: a `## Summary` (bulleted, what changed and why) and a `## Test plan`
  (checked items for what was actually verified, unchecked for what still needs
  verification).
- Merge strategy: an actual merge commit — never squash, never rebase.
- **Do not delete the branch after merging.** See
  [`operations/release-process.md`](operations/release-process.md#why-keep-merged-branches-around)
  for why.

## Releases

Tagged after merge, not before — see
[`operations/release-process.md`](operations/release-process.md) for the full flow.

## Documentation

Every layer, model, and integration in this project has a corresponding document
under `docs/`. When adding a new model or changing an existing one's behavior, update
its doc in the same PR — documentation drift is a bug like any other.

## Related

- [`operations/release-process.md`](operations/release-process.md)
- [`operations/runbook.md`](operations/runbook.md)
