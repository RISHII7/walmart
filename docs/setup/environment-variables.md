# Environment Variables Reference

Every secret and machine-specific value in this project is read from environment
variables or gitignored local files — nothing is hardcoded into version-controlled
source. This page is the single reference for what exists, where it's set, and what
consumes it.

## Root project — `.env` (gitignored)

| Variable | Consumed by | Purpose |
|---|---|---|
| `POSTGRES_CONNECTION_STRING` | `walmart_dataset/load_data.py` | Raw-layer Postgres connection |

## dbt — `~/.dbt/profiles.yml` (never committed)

| Field | Purpose |
|---|---|
| `host` | Databricks SQL Warehouse hostname |
| `http_path` | SQL Warehouse HTTP path |
| `token` | Personal access token |
| `catalog` / `schema` | Default Unity Catalog target |

See [`databricks-unity-catalog-setup.md`](databricks-unity-catalog-setup.md) for the
full connection format.

## Airflow — `walmart-dbt/.env` (gitignored)

| Variable | Consumed by | Purpose |
|---|---|---|
| `AIRFLOW_UID` | `docker-compose.yaml` (`user:` on every service) | Matches container file ownership to the host user, avoiding root-owned volume files on Linux |
| `FERNET_KEY` | `AIRFLOW__CORE__FERNET_KEY` | Encrypts connection passwords / secret Variables at rest in Airflow's metadata DB |
| `DATABRICKS_HOST` | `dags/orchestrate.py` (`ingest_cdc`) | Databricks workspace URL for the ingestion job trigger |
| `DATABRICKS_TOKEN` | `dags/orchestrate.py` (`ingest_cdc`) | Personal access token for the same |
| `DATABRICKS_JOB_ID` | `dags/orchestrate.py` (`ingest_cdc`) | The Databricks job `ingest_cdc` triggers |

**A note on `FERNET_KEY`:** with it unset, Airflow runs but silently skips encryption
of anything stored via Connections/Variables — functionally fine for a local dev
stack where nothing else has access to the Postgres metadata DB, but worth setting
properly (`python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"`)
before storing anything genuinely sensitive through the Airflow UI.

## Airflow's own compose-level defaults

A few more variables have safe defaults baked into `docker-compose.yaml` itself via
`${VAR:-default}` syntax, and only need overriding for non-default setups:
`_AIRFLOW_WWW_USER_USERNAME` / `_AIRFLOW_WWW_USER_PASSWORD` (default `airflow`/`airflow`),
`AIRFLOW__API_AUTH__JWT_SECRET`, `AIRFLOW__API_AUTH__JWT_ISSUER`.

## Rule this project follows

If a value is a secret, a credential, or something that legitimately differs between
machines, it goes in a gitignored `.env` file or a gitignored config file
(`profiles.yml`), never directly in a tracked file — this has been enforced
consistently (`.gitignore` explicitly excludes `.env`, `connection.txt`,
`profiles.yml`, and `airflow.cfg` across this repository) precisely because
credentials committed to git history are effectively permanent, even if removed in a
later commit.

## Related

- [`postgres-setup.md`](postgres-setup.md)
- [`databricks-unity-catalog-setup.md`](databricks-unity-catalog-setup.md)
- [`../airflow/docker-setup.md`](../airflow/docker-setup.md)
