# DAG Reference: `orchestrate`

Operational detail for every task in `walmart-dbt/dags/orchestrate.py` — what it does,
what failure looks like, and what to check first.

## `ingest_cdc`

| | |
|---|---|
| **Type** | `@task` (Python, TaskFlow) |
| **Depends on** | nothing (first task) |
| **What it does** | Triggers a Databricks job via `WorkspaceClient.jobs.run_now()`, polls every 5s until terminal |
| **Config source** | `DATABRICKS_HOST`, `DATABRICKS_TOKEN`, `DATABRICKS_JOB_ID` env vars |
| **Failure modes** | Bad/expired token → auth error immediately; job fails on the Databricks side → `Exception("Job failed with state: ...")` raised from the polling loop; job runs indefinitely → this task blocks until the job itself reaches a terminal state (no task-level timeout is currently configured) |
| **First thing to check on failure** | The referenced Databricks job's own run history in the Databricks UI — this task only reports the *result*, the actual failure detail lives in the job run |

## `clean_target`

| | |
|---|---|
| **Type** | `@task.bash` |
| **Depends on** | `ingest_cdc` |
| **What it does** | `rm -rf /opt/airflow/walmart/target && rm -rf /opt/airflow/walmart/logs` |
| **Failure modes** | Extremely low — only fails if the container's filesystem is unwritable |

## `source_freshness`

| | |
|---|---|
| **Type** | `@task.bash` |
| **Depends on** | `clean_target` |
| **What it does** | `cd /opt/airflow/walmart && dbt source freshness` |
| **Failure modes** | Bronze hasn't been refreshed within the configured freshness threshold; Databricks connection issue |
| **First thing to check on failure** | Whether `ingest_cdc`'s upstream Databricks job actually refreshed bronze — a freshness failure right after a successful `ingest_cdc` points at a mismatch between what that job touches and what `sources.yml` expects |

## `silver_technical`

| | |
|---|---|
| **Type** | `BashOperator` |
| **Depends on** | `source_freshness` |
| **Command** | `dbt run --select silver_t` |
| **Builds** | `customers_t`, `employees_t`, `order_items_t`, `orders_t`, `products_t`, `stores_t` |
| **Failure modes** | A bronze schema change breaking a `SELECT *`; Databricks compute/warehouse unavailable |

## `silver_technical_tests`

| | |
|---|---|
| **Type** | `BashOperator` |
| **Depends on** | `silver_technical` |
| **Command** | `dbt test --select silver_t` |
| **Checks** | `not_null`/`unique` on `products_t.product_id` and `orders_t.order_id` |
| **Failure modes** | A duplicated or null primary key made it into bronze |

## `silver_business`

| | |
|---|---|
| **Type** | `BashOperator` |
| **Depends on** | `silver_technical_tests` |
| **Command** | `dbt run --select silver_b` |
| **Builds** | `obt_b` |
| **Failure modes** | Any of the six `silver_t` tables not yet built/stale |

## `silver_business_tests`

| | |
|---|---|
| **Type** | `BashOperator` |
| **Depends on** | `silver_business` |
| **Command** | `dbt test --select silver_b` |
| **Checks** | `test_obt` — null join keys on `obt_b` (warn severity — does not fail the run) |

## `gold_ephermeral`

| | |
|---|---|
| **Type** | `BashOperator` |
| **Depends on** | `silver_business_tests` |
| **Command** | `dbt run --select gold/ephemeral` |
| **Builds** | Compiles `eph_customers`, `eph_employees`, `eph_orders`, `eph_products`, `eph_stores` (ephemeral — no persisted output from this step alone) |

## `gold_dimensions`

| | |
|---|---|
| **Type** | `BashOperator` |
| **Depends on** | `gold_ephermeral` |
| **Command** | `dbt snapshot` |
| **Builds** | `dim_customers`, `dim_employees`, `dim_orders`, `dim_products`, `dim_stores` |
| **Failure modes** | A snapshot's `unique_key` producing duplicates in a single run (would violate the snapshot's assumptions) |

## `gold_facts`

| | |
|---|---|
| **Type** | `BashOperator` |
| **Depends on** | `gold_dimensions` |
| **Command** | `dbt run --select gold/fact` |
| **Builds** | `fact_orders` |

## Retry and alerting

No custom `retries`/`retry_delay` are configured on any task in this DAG — they use
Airflow's defaults. Given the linear dependency chain, a mid-pipeline failure (e.g. at
`silver_business`) leaves earlier tables (`silver_t`) already rebuilt and later ones
(`gold`) untouched from the previous run — safe to simply re-run the DAG from the
failed task via the Airflow UI ("Clear" on the failed task) rather than a full restart.

## Related

- [`orchestration-guide.md`](orchestration-guide.md)
- [`../operations/runbook.md`](../operations/runbook.md)
- [`../operations/troubleshooting.md`](../operations/troubleshooting.md)
