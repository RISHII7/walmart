# Model: `eph_orders`

**Layer:** gold/ephemeral · **Materialization:** ephemeral (compiled inline) · **Grain:** one row per `order_id` (plus a bridge key)

## Purpose

Deduplicates the order entity back out of `silver_b.obt_b`, undoing the fan-out
caused by one order having many order items.

## SQL

```sql
SELECT DISTINCT
    order_id,
    order_item_id,
    payment_method,
    order_status,
    order_timestamp,
    order_created_timestamp,
    order_updated_timestamp,
    order_is_active,
    order_processed_at,
    obt_b_processed_at,
    CURRENT_TIMESTAMP() AS order_gold_processed_at
FROM {{ ref('obt_b') }}
```

## The one dimension that isn't purely a dimension

Unlike the other four ephemeral models, `eph_orders` also carries `order_item_id`.
This is intentional: it acts as a bridge key back to the OBT's true grain, which is
useful for downstream consumers that need to relate an order-level dimension row back
to the specific line items it came from, without re-joining `obt_b` directly.

## Materialization note

`ephemeral`: never persisted, inlined wherever referenced — only in
[`dim_orders`](../../../../walmart-dbt/walmart/snapshots/dim_orders.yml).

## Downstream consumers

- `gold.dim_orders` (snapshot, SCD Type 2)

## Related

- [`../../../data-model/gold-layer.md`](../../../data-model/gold-layer.md)
- [`../snapshots/dim_orders.md`](../snapshots/dim_orders.md)
