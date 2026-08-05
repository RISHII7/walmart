# Model: `stores_t`

**Layer:** silver_t · **Materialization:** incremental table · **Schema:** `silver_t` · **Grain:** one row per `store_id`

## Purpose

Incrementally mirrors `bronze.stores` into the silver technical layer.

## SQL

```sql
{{ config(materialized='incremental', unique_key='store_id') }}

SELECT *, current_timestamp() AS processed_at
FROM {{ source('walmart_databricks', 'stores') }}

{% if is_incremental() %}
WHERE updated_timestamp > (
    SELECT COALESCE(MAX(updated_timestamp), '1900-01-01') FROM {{ this }}
)
{% endif %}
```

## Columns

All columns from `bronze.stores` (`store_id`, `store_name`, `city`, `province`,
`country`, `created_timestamp`, `updated_timestamp`, `is_active`), plus
`processed_at`.

## Incremental behavior

- **`unique_key`:** `store_id`
- **Watermark column:** `updated_timestamp`

## Downstream consumers

- `silver_b.obt_b` (joined as alias `s`, on `o.store_id = s.store_id`)
- Indirectly shapes `employees_t`'s join too, since employees are joined into the OBT
  via the order's `store_id`, not the employee's own store record directly.

## Related

- [`../../project-guide.md`](../../project-guide.md)
- [`../../../data-model/data-dictionary.md`](../../../data-model/data-dictionary.md)
