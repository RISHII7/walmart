# Operations Runbook

## Daily / per-run checks

1. **Did the `orchestrate` DAG run succeed?** Airflow UI → DAGs → `orchestrate` →
   check the latest run's status. A failure at any task blocks everything downstream
   of it (see [`../airflow/dag-reference.md`](../airflow/dag-reference.md) for the
   dependency chain).
2. **Did `source_freshness` pass?** If bronze hasn't been refreshed recently enough,
   this is the earliest signal — check `ingest_cdc`'s upstream Databricks job first.
3. **Did any data test fail or warn?** `silver_technical_tests` (error severity — blocks
   the run) and `silver_business_tests` (warn severity on `test_obt` — logs but doesn't
   block) both report in the task logs.

## Common operational tasks

### Re-running the pipeline from a specific stage

Clear the failed task (and everything downstream) from the Airflow UI's Grid view, or
from the CLI:

```bash
docker compose exec airflow-apiserver airflow tasks clear orchestrate -t <task_id> -s <run_date>
```

### Forcing a full rebuild of a silver_t table

Needed whenever a model's filter/business logic changes and must apply retroactively
to already-materialized rows (see
[`../architecture/data-flow.md`](../architecture/data-flow.md#incremental-behavior)):

```bash
cd walmart-dbt/walmart
dbt run --select <model_name> --full-refresh
```

### Checking what a snapshot actually captured

```bash
dbt show --inline "SELECT * FROM {{ ref('dim_customers') }} WHERE dbt_valid_to = '9999-12-31' LIMIT 10"
```

### Manually triggering the DAG

```bash
docker compose exec airflow-apiserver airflow dags trigger orchestrate
```

### Restarting a specific Airflow service

```bash
docker compose restart airflow-scheduler
```

### Rebuilding the Airflow image after a dependency change

```bash
cd walmart-dbt
docker compose build --no-cache
docker compose up -d
```

## Escalation checklist

If a DAG run fails and the cause isn't obvious from the task logs:

1. Check [`troubleshooting.md`](troubleshooting.md) for a matching symptom first.
2. Confirm the Databricks SQL Warehouse is running and reachable (`dbt debug` from
   inside a worker container, or locally against the same profile).
3. Confirm bronze actually has fresh data — a pipeline can run "successfully" while
   silently processing stale bronze if the upstream ingestion job failed silently.
4. Check `docker compose ps` for any service not reporting healthy.

## Related

- [`troubleshooting.md`](troubleshooting.md)
- [`release-process.md`](release-process.md)
- [`../airflow/dag-reference.md`](../airflow/dag-reference.md)
