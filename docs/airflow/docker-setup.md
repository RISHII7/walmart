# Airflow Docker Setup

## Overview

The Airflow deployment lives entirely in `walmart-dbt/` as a Docker Compose stack:
Celery-based Airflow, backed by its own Postgres metadata database and a Redis
broker, running a custom image extended with the dbt and Databricks tooling the DAG
needs.

## The image

`walmart-dbt/Dockerfile`:

```dockerfile
FROM apache/airflow:3.2.2

USER root
RUN apt-get update && apt-get install -y gcc && apt-get clean
USER airflow

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
```

`requirements.txt` pins `apache-airflow==3.2.2` **exactly**, matching the base image
version precisely — this is deliberate, not incidental. An unpinned floor
(`apache-airflow>=3.2.2`) lets pip silently install a newer point release with a
provider ecosystem (Celery, in particular) that hasn't necessarily kept pace,
producing runtime `ImportError`s that only surface once a container actually starts,
not at build time. Pinning to exactly what the base image ships means `pip install`
recognizes airflow-core as "already satisfied" and never touches it or its
already-consistent provider set. Alongside it: `databricks-sdk` (used directly by the
`ingest_cdc` task) and the dbt tooling (`dbt-core`, `dbt-databricks`).

## Services (`docker-compose.yaml`)

| Service | Command | Notes |
|---|---|---|
| `postgres` | — | Airflow metadata DB (`postgres:16`) |
| `redis` | — | Celery broker (`redis:7.2-bookworm`) |
| `airflow-apiserver` | `api-server` | Web UI + REST API, `localhost:8080` |
| `airflow-scheduler` | `scheduler` | |
| `airflow-dag-processor` | `dag-processor` | Parses DAG files independently of the scheduler |
| `airflow-worker` | `celery worker` | Executes tasks |
| `airflow-triggerer` | `triggerer` | Deferred/async task support |
| `airflow-init` | one-shot script | DB migration, default user creation, volume ownership fixup |
| `airflow-cli` | (debug profile) | Ad hoc `airflow` CLI access |
| `flower` | (flower profile) | Celery monitoring UI, `localhost:5555` |

All Airflow services share environment and volumes via the `x-airflow-common` YAML
anchor, avoiding repetition across seven near-identical service definitions.

## Environment configuration

`AIRFLOW__CORE__EXECUTOR: CeleryExecutor`, a FastAPI-based simple auth manager
(`AIRFLOW__CORE__AUTH_MANAGER`), and a custom `AIRFLOW_CONFIG` pointing at a
version-controllable `airflow.cfg` under `config/`. Secrets and machine-specific
values (`FERNET_KEY`, `AIRFLOW_UID`, Databricks credentials) come from
`walmart-dbt/.env`, loaded via each service's `env_file` directive — never hardcoded
in `docker-compose.yaml` itself.

## Volumes

| Host path | Container path |
|---|---|
| `dags/` | `/opt/airflow/dags` |
| `logs/` | `/opt/airflow/logs` |
| `config/` | `/opt/airflow/config` |
| `plugins/` | `/opt/airflow/plugins` |
| `walmart/` | `/opt/airflow/walmart` |

The last mount is what makes the dbt project available inside every Airflow
container at the exact path the DAG's `BashOperator` tasks expect
(`cwd='/opt/airflow/walmart'`).

## Bringing it up

```bash
cd walmart-dbt
docker compose up -d          # first run also triggers airflow-init
docker compose ps              # verify every service reports healthy
```

Access the UI at `http://localhost:8080` (default credentials from `.env`'s
`_AIRFLOW_WWW_USER_USERNAME` / `_AIRFLOW_WWW_USER_PASSWORD`, `airflow`/`airflow` unless
overridden).

## Related

- [`orchestration-guide.md`](orchestration-guide.md)
- [`../setup/environment-variables.md`](../setup/environment-variables.md)
- [`../operations/troubleshooting.md`](../operations/troubleshooting.md)
