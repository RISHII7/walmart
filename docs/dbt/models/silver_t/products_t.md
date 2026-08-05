# Model: `products_t`

**Layer:** silver_t · **Materialization:** incremental table · **Schema:** `silver_t` · **Grain:** one row per `product_id`

## Purpose

Incrementally mirrors `bronze.products` into the silver technical layer.

## SQL

```sql
{{ config(materialized='incremental', unique_key='product_id') }}

SELECT *, current_timestamp() AS processed_at
FROM {{ source('walmart_databricks', 'products') }}

{% if is_incremental() %}
WHERE updated_timestamp > (
    SELECT COALESCE(MAX(updated_timestamp), '1900-01-01') FROM {{ this }}
)
{% endif %}
```

## Columns

All columns from `bronze.products` (`product_id`, `product_name`, `category`,
`brand`, `price`, `created_timestamp`, `updated_timestamp`, `is_active`), plus
`processed_at`.

## Incremental behavior

- **`unique_key`:** `product_id`
- **Watermark column:** `updated_timestamp`
- Carries [`data_tests`](../../testing-strategy.md) — `not_null` on `product_id`,
  and `unique` scoped to `where: "price > 0"` (a duplicate free-sample or
  zero-priced product row wouldn't corrupt reporting the way a duplicate priced
  product would).

## Downstream consumers

- `silver_b.obt_b` (joined as alias `p`, on `oi.product_id = p.product_id` — i.e.
  joined via order_items, not directly to orders)

## Related

- [`../../project-guide.md`](../../project-guide.md)
- [`../../testing-strategy.md`](../../testing-strategy.md)
