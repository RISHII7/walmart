# walmart-dbt

The transformation and orchestration half of the platform: a dbt project targeting
Databricks, plus the Airflow deployment that runs it end to end.

For the full picture — architecture, data model, setup, and operations — see
[`../docs/`](../docs/architecture/overview.md). This file covers just what's specific
to this directory.

## Layout

```text
walmart-dbt/
├── walmart/                # the dbt project itself
│   ├── models/
│   │   ├── source/          # bronze source declarations
│   │   ├── silver_t/        # incremental silver models
│   │   ├── silver_b/        # the One Big Table
│   │   └── gold/             # ephemeral dimensions + fact table
│   ├── snapshots/            # SCD Type 2 dimension history
│   ├── tests/                 # custom data tests
│   └── macros/                 # custom_schema.sql
├── dags/
│   └── orchestrate.py           # the end-to-end Airflow DAG
├── docker-compose.yaml           # Airflow (Celery, Redis, Postgres metadata DB)
├── Dockerfile                     # Airflow image + dbt-core + dbt-databricks
└── requirements.txt
```

## Quick reference

```bash
# dbt (from walmart/)
cd walmart
dbt run && dbt test && dbt snapshot

# Airflow (from here)
docker compose up -d
```

## Documentation

- [`../docs/dbt/project-guide.md`](../docs/dbt/project-guide.md) — the dbt project in depth
- [`../docs/airflow/orchestration-guide.md`](../docs/airflow/orchestration-guide.md) — the DAG and how it's deployed
- [`../docs/setup/local-development.md`](../docs/setup/local-development.md) — full setup walkthrough
- [`../docs/operations/troubleshooting.md`](../docs/operations/troubleshooting.md) — known issues and fixes
