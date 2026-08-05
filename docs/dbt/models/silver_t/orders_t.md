# Model: `orders_t`

**Layer:** silver_t · **Materialization:** incremental table · **Schema:** `silver_t` · **Grain:** one row per `order_id`

## Purpose

Incrementally mirrors `bronze.orders`. This is the model `silver_b.obt_b` uses as its
join anchor — every other entity in the OBT is joined *against* this one.

## SQL

```sql
{{ config(materialized='incremental', unique_key='order_id') }}

SELECT *, current_timestamp() AS processed_at
FROM {{ source('walmart_databricks', 'orders') }}

{% if is_incremental() %}
WHERE updated_timestamp > (
    SELECT COALESCE(MAX(updated_timestamp), '1900-01-01') FROM {{ this }}
)
{% endif %}
```

## Columns

All columns from `bronze.orders` (`order_id`, `customer_id`, `store_id`,
`order_timestamp`, `payment_method`, `order_status`, `total_amount`,
`created_timestamp`, `updated_timestamp`, `is_active`), plus `processed_at`.

## Incremental behavior

- **`unique_key`:** `order_id`
- **Watermark column:** `updated_timestamp`
- This table also carries [`data_tests`](../../testing-strategy.md) — `not_null` and
  `unique` on `order_id` — since a duplicated or missing order ID would corrupt every
  downstream join in `obt_b`.

## Downstream consumers

- `silver_b.obt_b` (aliased `o` — the anchor table every other entity joins against)

## Related

- [`../../project-guide.md`](../../project-guide.md)
- [`../../testing-strategy.md`](../../testing-strategy.md)
- [`../silver_b/obt_b.md`](../silver_b/obt_b.md)
