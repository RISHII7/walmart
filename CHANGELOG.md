# Changelog

All notable changes to this project are documented here. Versions follow a
minor-increment scheme (`v0.x.0`) tied to each mergeable unit of work — see
[`docs/operations/release-process.md`](docs/operations/release-process.md) for the
full release workflow.

## v0.6.0 — Orchestrate DAG for the full bronze-to-gold pipeline

- `dags/orchestrate.py`: the complete Airflow DAG — `ingest_cdc` → `clean_target` →
  `source_freshness` → `silver_t` run/test → `silver_b` run/test → gold ephemeral →
  gold snapshots → gold facts.

## v0.5.0 — Fix Airflow/dbt dependency conflict

- Removed an Airflow-2.x-only third-party operators package that had no working
  release for Airflow 3.x at all, and that nothing in the project's own DAGs
  actually imported.
- Pinned `apache-airflow` to the exact version matching the Docker base image,
  fixing a provider/core version mismatch that was crash-looping the scheduler and
  worker.
- Added `databricks-sdk` as an explicit dependency (used directly by the
  orchestration DAG).
- Renamed the dbt project's container mount path for clarity.

## v0.4.0 — Airflow orchestration scaffold

- Added the full Airflow CeleryExecutor stack (`docker-compose.yaml`): Redis broker,
  Postgres metadata database, apiserver, scheduler, dag-processor, worker, triggerer.
- Custom `Dockerfile` extending the base Airflow image with `dbt-core` and
  `dbt-databricks` so DAG tasks can invoke `dbt` directly.
- Fixed a volume-mount path mismatch discovered before this was ever run: mount
  targets didn't match where Airflow's own configuration and setup script expected
  files to live.
- Hardened `.gitignore` against `airflow.cfg`, which carries live encryption/session
  secrets when generated locally.

## v0.3.0 — Full silver/gold dbt pipeline on Databricks

- **Silver layer:** incremental models for all six bronze source tables.
- **`silver_b.obt_b`:** the One Big Table join across the silver layer.
- **Gold layer:** ephemeral per-entity dimension models deduplicated out of the OBT,
  SCD Type 2 snapshots tracking full dimension history, and `fact_orders` completing
  a standard star schema.
- A data test flagging null join keys in the OBT.

## v0.2.0 — dbt + Databricks project scaffold

- `dbt-core` and `dbt-databricks` added as project dependencies.
- The `dbt init`-scaffolded project (structure, example models, standard folders)
  committed and wired to a Databricks SQL Warehouse target.
- `.gitignore` hardened to exclude local secrets and dbt build artifacts.

## v0.1.0 — Initial project scaffold

- uv-managed Python 3.13 project structure.
- `raw` schema DDL for the six core entities (customers, stores, products,
  employees, orders, order_items).
- Source dataset CSVs.
- `load_data.py`, using `psycopg` 3's `COPY` API to bulk-load the CSVs into
  PostgreSQL.
