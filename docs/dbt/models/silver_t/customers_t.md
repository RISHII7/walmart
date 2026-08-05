# Model: `customers_t`

**Layer:** silver_t · **Materialization:** incremental table · **Schema:** `silver_t` · **Grain:** one row per `customer_id`

## Purpose

Incrementally mirrors `bronze.customers` into the silver technical layer, stamping
each row with when it was last processed.

## SQL

```sql
{{ config(materialized='incremental', unique_key='customer_id') }}

SELECT *, current_timestamp() AS processed_at
FROM {{ source('walmart_databricks', 'customers') }}

{% if is_incremental() %}
WHERE updated_timestamp > (
    SELECT COALESCE(MAX(updated_timestamp), '1900-01-01') FROM {{ this }}
)
{% endif %}
```

## Columns

All columns from `bronze.customers` (`customer_id`, `first_name`, `last_name`,
`email`, `phone`, `city`, `province`, `country`, `created_timestamp`,
`updated_timestamp`, `is_active`), plus `processed_at`.

## Incremental behavior

- **`unique_key`:** `customer_id`
- **Watermark column:** `updated_timestamp`
- On a normal run, only customers whose `updated_timestamp` is newer than the max
  already in the table get (re)loaded.
- A logic change here (e.g. adding a filter) needs `dbt run --select customers_t --full-refresh`
  to apply retroactively — see [`../../../architecture/data-flow.md`](../../../architecture/data-flow.md#incremental-behavior).

## Downstream consumers

- `silver_b.obt_b` (joined as alias `c`, on `o.customer_id = c.customer_id`)

## Related

- [`../../project-guide.md`](../../project-guide.md)
- [`../../../data-model/data-dictionary.md`](../../../data-model/data-dictionary.md)
