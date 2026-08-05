# Troubleshooting Guide

Real issues encountered while building and running this platform, and how they were
actually resolved.

## Airflow / dbt dependency conflicts

**Symptom:** `airflow-worker` and `airflow-scheduler` crash-loop after a Docker build,
with errors like `ImportError: cannot import name 'execute_callback_workload'` or
`AirflowConfigException: The module/attribute could not be loaded... Current value:
":CeleryExecutor:"`.

**Cause:** a floating version constraint (`apache-airflow>=3.2.2` rather than an
exact pin) let `pip` resolve a newer Airflow core release than the one the Celery
provider (or another provider) was actually tested against. The mismatch only
surfaces at container runtime, not at build time.

**Fix:** pin `apache-airflow` to the **exact** version matching the base image
(`FROM apache/airflow:3.2.2` → `apache-airflow==3.2.2` in `requirements.txt`). Once
pinned exactly, `pip install` recognizes airflow-core as already satisfied and never
touches it or its already-consistent bundled providers — no separate constraints file
needed. (An official Airflow constraints file *can* help pin providers precisely, but
applying it wholesale to a `requirements.txt` that also installs unrelated packages
like `dbt-core` can introduce a different conflict — see the next entry.)

## A dbt dependency conflicting with Airflow's constraints file

**Symptom:** `pip install -r requirements.txt --constraint <airflow-constraints-url>`
fails with something like `dbt-core depends on pathspec<1.1... The user requested
(constraint) pathspec==1.1.1`.

**Cause:** Airflow's official constraints file pins versions for *every* package it
touches, including common transitive dependencies (`pathspec`, `requests`, etc.) —
applying it to a `requirements.txt` that also installs `dbt-core` forces `dbt-core`
into a version of a shared dependency it explicitly doesn't support.

**Fix:** don't apply the constraints file at all once `apache-airflow` is pinned to
match the base image exactly (see above) — the constraints file's only real purpose,
protecting against Airflow-side version drift, is already covered by the exact pin.

## A dependency with no working version for the Airflow major version in use

**Symptom:** `pip`'s resolver reports something like `package X depends on
apache-airflow<3.0.0` no matter which Airflow 3.x patch version is specified.

**Cause:** the package genuinely has no release compatible with the Airflow major
version in use — this isn't a pinning problem, it's a hard incompatibility.

**Fix:** check whether anything in the project's own DAGs actually imports the
package before spending more time on it — if nothing does, remove it. If specific
functionality from it is genuinely needed, vendor just that functionality directly
into the project (copy the relevant source in) rather than carrying a dependency
that can never resolve cleanly.

## Stale dbt partial-parse cache causing a `KeyError` on Windows

**Symptom:** `dbt parse` / `dbt run` fails with something like
`KeyError: 'walmart://macros\\custom_schema.sql'` — a file-ID lookup failing inside
dbt's manifest loader.

**Cause:** dbt caches parsed project state in `target/partial_parse.msgpack` to speed
up subsequent runs. On Windows, a file ID cached with backslash-style path separators
can stop matching the forward-slash-normalized ID dbt expects on a later run,
especially after project files move or the environment changes.

**Fix:** delete the `target/` directory and re-parse (`dbt parse` or `dbt run`) to
force a full reparse and regenerate a consistent cache. `target/` is already
gitignored — this is always a safe, non-destructive fix.

## Docker volume mount path mismatch

**Symptom:** DAGs/logs/config placed on the host never appear where Airflow expects
them inside the container; `dbt` commands in `BashOperator` tasks fail with
"directory not found" even though the mount looks correct in `docker-compose.yaml`.

**Cause:** Airflow's `AIRFLOW_HOME` defaults to `/opt/airflow` inside the base image
and is used throughout (`AIRFLOW_CONFIG`, the `airflow-init` service's own setup
script). If a volume mount's container-side target is changed to something else
without updating every other reference to match, the container ends up with two
disconnected directory trees — the mounted one (never read by Airflow) and the
expected one (empty, since nothing's mounted there).

**Fix:** keep every path reference — volume targets, `AIRFLOW_CONFIG`, DAG file
`cwd`/`cd` commands — pointed at the same base path consistently. When intentionally
renaming a mount, grep the whole `docker-compose.yaml` and every DAG file for the old
path before assuming the rename is complete.

## `FERNET_KEY` unset warning

**Symptom:** `The "FERNET_KEY" variable is not set. Defaulting to a blank string.`
repeated once per Airflow service on `docker compose up`.

**Cause:** `AIRFLOW__CORE__FERNET_KEY: ${FERNET_KEY}` has no fallback default and no
`.env` value is set.

**Fix:** generate one and add it to `walmart-dbt/.env`:

```bash
python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"
```

Not committing anything with this unset doesn't break the stack — it just means
Airflow skips encrypting Connections/Variables, which matters once real credentials
are stored through the Airflow UI rather than passed as DAG-level env vars.

## Accidentally committing a credential

**Symptom:** `git push` rejected by GitHub with `GH013: Repository rule violations...
Push cannot contain secrets`.

**Cause:** GitHub's secret-scanning push protection detected a recognizable
credential pattern (API token, connection string, etc.) in a commit's diff.

**Fix:** if the credential is already invalid, GitHub provides a one-time "allow this
secret" link to push anyway — use it deliberately, not reflexively. If the credential
is live, remove it from the commit (amend if it was never pushed anywhere yet — safe,
since nothing shared has that history; a fresh commit on top if it *has* been pushed,
since the secret would otherwise persist in history regardless of a later fix) and
rotate the credential regardless of which path is taken.

## Local IDE extension errors on `.sql`/DAG files

**Symptom:** an IDE dbt/Airflow extension reports an import or syntax error that
doesn't reproduce when running the equivalent command directly (`dbt parse`, `dbt
show`, etc.) via the CLI.

**Cause:** IDE extensions frequently run their own bundled Python environment or
static-analysis pass, separate from the project's actual virtual environment — a
missing package or version mismatch there doesn't necessarily mean anything is wrong
with the project itself.

**Fix:** always verify against the actual CLI in the actual project environment
before treating an editor diagnostic as ground truth.

## Related

- [`runbook.md`](runbook.md)
- [`../airflow/dag-reference.md`](../airflow/dag-reference.md)
