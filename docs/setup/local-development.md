# Local Development Setup

Complete, ordered steps to bring the whole platform up from a clean checkout.

## Prerequisites

- Python 3.13 and [`uv`](https://docs.astral.sh/uv/)
- Docker Desktop (or equivalent), for the Airflow stack
- Access to a PostgreSQL instance (local or hosted)
- A Databricks workspace with Unity Catalog enabled, and a personal access token
- (Optional, for the `reviews` ingestion path) An AWS account with S3 access

## 1. Python environment

The repository is a `uv` workspace: the root project plus `walmart-dbt/` as a
member, sharing one virtual environment.

```bash
uv sync
```

## 2. Raw layer — PostgreSQL

```bash
# .env at the repo root
echo 'POSTGRES_CONNECTION_STRING="postgresql://user:password@host:port/dbname?sslmode=require"' > .env

psql "$POSTGRES_CONNECTION_STRING" -f walmart_dataset/ddl/walmart_schema.sql
cd walmart_dataset
uv run python load_data.py
cd ..
```

Full detail: [`postgres-setup.md`](postgres-setup.md)

## 3. Databricks + Unity Catalog

Provision (or connect to an existing) `walmart` catalog with `bronze`, `silver_t`,
`silver_b`, and `gold` schemas, and a SQL Warehouse. Populate
`~/.dbt/profiles.yml`:

```yaml
walmart:
  outputs:
    dev:
      type: databricks
      catalog: walmart
      host: <workspace-host>
      http_path: /sql/1.0/warehouses/<warehouse-id>
      schema: dbt_schema
      threads: 1
      token: <personal-access-token>
  target: dev
```

Verify:

```bash
cd walmart-dbt/walmart
dbt debug
```

Full detail: [`databricks-unity-catalog-setup.md`](databricks-unity-catalog-setup.md)

## 4. (Optional) S3 integration for the `reviews` feed

If you want the supplementary reviews ingestion path, provision the Unity Catalog
external location and S3 bucket as described in [`s3-integration.md`](s3-integration.md).
This is independent of the core pipeline — everything else works without it.

## 5. Build the dbt pipeline

```bash
cd walmart-dbt/walmart
dbt run --select silver_t
dbt test --select silver_t
dbt run --select silver_b
dbt test --select silver_b
dbt run --select gold/ephemeral
dbt snapshot
dbt run --select gold/fact
```

Full detail: [`../dbt/project-guide.md`](../dbt/project-guide.md)

## 6. Bring up Airflow

```bash
cd walmart-dbt

# .env for the Airflow stack
cat > .env <<'EOF'
AIRFLOW_UID=50000
FERNET_KEY=<generate one — see environment-variables.md>
DATABRICKS_HOST=<workspace-host>
DATABRICKS_TOKEN=<personal-access-token>
DATABRICKS_JOB_ID=<job-id>
EOF

docker compose up -d
docker compose ps    # confirm every service is healthy
```

UI at `http://localhost:8080`. Full detail: [`../airflow/docker-setup.md`](../airflow/docker-setup.md)

## 7. Run the pipeline end to end

Unpause and trigger the `orchestrate` DAG from the Airflow UI, or:

```bash
docker compose exec airflow-apiserver airflow dags trigger orchestrate
```

## Troubleshooting

If anything here doesn't come up cleanly on the first try, check
[`../operations/troubleshooting.md`](../operations/troubleshooting.md) before
digging further — it covers the specific failure modes this stack is prone to
(dependency version drift between Airflow/dbt/Celery, stale dbt partial-parse caches,
credentials committed accidentally, and a few others).

## Related

- [`environment-variables.md`](environment-variables.md) — every variable, in one place
- [`../architecture/overview.md`](../architecture/overview.md) — what all of this is actually building toward
