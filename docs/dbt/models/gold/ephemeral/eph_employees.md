# Model: `eph_employees`

**Layer:** gold/ephemeral · **Materialization:** ephemeral (compiled inline) · **Grain:** one row per `employee_id`

## Purpose

Deduplicates the employee entity back out of `silver_b.obt_b`, undoing the fan-out
caused by one employee appearing on every order handled at their store.

## SQL

```sql
SELECT DISTINCT
    employee_id,
    employee_first_name,
    employee_last_name,
    employee_email,
    job_title,
    salary,
    store_id,
    employee_created_timestamp,
    employee_updated_timestamp,
    employee_is_active,
    employee_processed_at,
    CURRENT_TIMESTAMP() AS employee_gold_processed_at
FROM {{ ref('obt_b') }}
```

Note this is the one ephemeral model that also carries `store_id` — the employee's
own foreign key, distinct from any order-level store attribution — giving the
downstream dimension a direct link back to `dim_stores`.

## Materialization note

`ephemeral`: never persisted, inlined wherever referenced — only in
[`dim_employees`](../../../../walmart-dbt/walmart/snapshots/dim_employees.yml).

## Downstream consumers

- `gold.dim_employees` (snapshot, SCD Type 2)

## Related

- [`../../../data-model/gold-layer.md`](../../../data-model/gold-layer.md)
- [`../snapshots/dim_employees.md`](../snapshots/dim_employees.md)
