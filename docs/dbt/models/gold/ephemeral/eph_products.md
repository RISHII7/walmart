# Model: `eph_products`

**Layer:** gold/ephemeral · **Materialization:** ephemeral (compiled inline) · **Grain:** one row per `product_id`

## Purpose

Deduplicates the product entity back out of `silver_b.obt_b`, undoing the fan-out
caused by one product appearing across many order line items.

## SQL

```sql
SELECT DISTINCT
    product_id,
    product_name,
    category,
    brand,
    price,
    product_created_timestamp,
    product_updated_timestamp,
    product_is_active,
    product_processed_at,
    CURRENT_TIMESTAMP() AS product_gold_processed_at
FROM {{ ref('obt_b') }}
```

## Materialization note

`ephemeral`: never persisted, inlined wherever referenced — only in
[`dim_products`](../../../../walmart-dbt/walmart/snapshots/dim_products.yml).

## Downstream consumers

- `gold.dim_products` (snapshot, SCD Type 2) — this is the dimension where price
  history matters most: a product's `price` changing is exactly the kind of
  slowly-changing attribute SCD Type 2 exists to capture.

## Related

- [`../../../data-model/gold-layer.md`](../../../data-model/gold-layer.md)
- [`../snapshots/dim_products.md`](../snapshots/dim_products.md)
