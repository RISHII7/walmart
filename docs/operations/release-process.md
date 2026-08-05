# Release Process

## Versioning

The project follows semantic-ish minor-version increments (`v0.x.0`) for each
meaningful, mergeable unit of work — a new pipeline layer, a fixed dependency
conflict, a new DAG. See [`../../CHANGELOG.md`](../../CHANGELOG.md) for the full
history.

## The flow, end to end

Every change — however small — goes through the same sequence, not a shortcut
straight to the default branch:

1. **Branch** off `main`: `feature/<name>`, `fix/<name>`, or `test/<name>`.
2. **Commit** with a message that explains *why*, not just *what changed* — the diff
   already shows what changed.
3. **Push** the branch and open a **pull request** against `main`, with a `## Summary`
   and `## Test plan`.
4. **Merge** with an actual merge commit (never squash or rebase) — this keeps the
   individual commit's own message intact in history alongside the PR reference.
5. **Keep the branch.** Feature branches are never deleted after merge — they stay on
   the remote as a record of the unit of work, even once merged.
6. **Tag a release** after the merge: an annotated tag (`vX.Y.Z`) with a message
   summarizing what shipped, pushed, then published as a GitHub release with fuller
   notes referencing the merged PR.

## Why keep merged branches around

A deleted branch after merge saves nothing meaningful (the commits are still in
`main`'s history either way) but does make it measurably harder to answer "what was
the actual set of changes in this unit of work, isolated from everything merged
before or after it" — `git log main..origin/feature/<name>` stops working the moment
the branch is gone. Keeping it costs nothing and preserves that.

## Release notes format

Each GitHub release lists:

- **What's included** — one bullet per merged PR in that release, linking the PR
- **Known open issues**, if any were deliberately left unresolved (rather than
  silently omitted)
- **Setup notes**, if the release changes how the project is run

## Related

- [`../CONTRIBUTING.md`](../CONTRIBUTING.md) — the branching/commit conventions this process assumes
- [`../../CHANGELOG.md`](../../CHANGELOG.md)
