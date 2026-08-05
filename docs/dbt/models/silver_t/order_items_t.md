# Model: `order_items_t`

**Layer:** silver_t · **Materialization:** incremental table · **Schema:** `silver_t` · **Grain:** one row per `order_item_id`

## Purpose

Incrementally mirrors `bronze.order_items` — the finest-grain entity in the entire
dataset, and the grain that `silver_b.obt_b` ultimately inherits.

## SQL

```sql
{{ config(materialized='incremental', unique_key='order_item_id') }}

SELECT *, current_timestamp() AS processed_at
FROM {{ source('walmart_databricks', 'order_items') }}

{% if is_incremental() %}
WHERE updated_timestamp > (
    SELECT COALESCE(MAX(updated_timestamp), '1900-01-01') FROM {{ this }}
)
{% endif %}
```

## Columns

All columns from `bronze.order_items` (`order_item_id`, `order_id`, `product_id`,
`quantity`, `unit_price`, `line_amount`, `created_timestamp`, `updated_timestamp`,
`is_active`), plus `processed_at`.

## Incremental behavior

- **`unique_key`:** `order_item_id`
- **Watermark column:** `updated_timestamp`

## Why this entity doesn't get its own gold dimension

Because the OBT's grain is already order-item level, there's no duplication to
collapse for this entity the way there is for customers, products, employees, or
stores (each of which repeats across many order items). Its measures
(`quantity`, `unit_price`, `line_amount`) flow directly into `gold.fact_orders`
instead of a dimension — see
[`../../../architecture/medallion-layers.md`](../../../architecture/medallion-layers.md#gold--conformed-business-facing-layer).

## Downstream consumers

- `silver_b.obt_b` (joined as alias `oi`, on `o.order_id = oi.order_id`)

## Related

- [`../../project-guide.md`](../../project-guide.md)
- [`../gold/fact/fact_orders.md`](../gold/fact/fact_orders.md)
