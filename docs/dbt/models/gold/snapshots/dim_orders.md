# Snapshot: `dim_orders`

**Layer:** gold (snapshot) · **Strategy:** timestamp · **Schema:** `gold` · **Grain:** one row per `order_id` per version

## Purpose

Captures full SCD Type 2 history of the order dimension — tracking changes to
`order_status` and `payment_method` over an order's lifecycle (e.g. pending → shipped
→ delivered) rather than only ever seeing its current state.

## Config

```yaml
snapshots:
  - name: dim_orders
    relation: ref('eph_orders')
    config:
      schema: gold
      database: walmart
      unique_key: order_id
      strategy: timestamp
      updated_at: order_updated_timestamp
      dbt_valid_to_current: "to_date('9999-12-31')"
```

## How it behaves

- **Source:** `eph_orders` (ephemeral)
- **Change detection:** compares `order_updated_timestamp` against what's already
  snapshotted for that `order_id`
- **Current-row marker:** `dbt_valid_to = '9999-12-31'`

## Columns

All columns from `eph_orders` (see [`../ephemeral/eph_orders.md`](../ephemeral/eph_orders.md)),
including the `order_item_id` bridge key, plus dbt's snapshot metadata: `dbt_scd_id`,
`dbt_updated_at`, `dbt_valid_from`, `dbt_valid_to`.

## Consumed by

`gold.fact_orders` joins to this dimension by `order_id`.

## Related

- [`../ephemeral/eph_orders.md`](../ephemeral/eph_orders.md)
- [`../../../data-model/gold-layer.md`](../../../data-model/gold-layer.md)
