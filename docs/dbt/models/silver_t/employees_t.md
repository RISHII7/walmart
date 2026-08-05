# Model: `employees_t`

**Layer:** silver_t · **Materialization:** incremental table · **Schema:** `silver_t` · **Grain:** one row per `employee_id`

## Purpose

Incrementally mirrors `bronze.employees` into the silver technical layer.

## SQL

```sql
{{ config(materialized='incremental', unique_key='employee_id') }}

SELECT *, current_timestamp() AS processed_at
FROM {{ source('walmart_databricks', 'employees') }}

{% if is_incremental() %}
WHERE updated_timestamp > (
    SELECT COALESCE(MAX(updated_timestamp), '1900-01-01') FROM {{ this }}
)
{% endif %}
```

## Columns

All columns from `bronze.employees` (`employee_id`, `store_id`, `first_name`,
`last_name`, `email`, `job_title`, `salary`, `created_timestamp`,
`updated_timestamp`, `is_active`), plus `processed_at`.

## Incremental behavior

- **`unique_key`:** `employee_id`
- **Watermark column:** `updated_timestamp`
- `store_id` is a plain foreign key here — no join happens in this model. The
  employee-to-store relationship is resolved later, in `obt_b`.

## Downstream consumers

- `silver_b.obt_b` (joined as alias `e`, on `o.store_id = e.store_id` — i.e. joined
  via the *order's* store, not directly to the employee's own store)

## Related

- [`../../project-guide.md`](../../project-guide.md)
- [`../../../data-model/data-dictionary.md`](../../../data-model/data-dictionary.md)
