# Snapshot: `dim_products`

**Layer:** gold (snapshot) · **Strategy:** timestamp · **Schema:** `gold` · **Grain:** one row per `product_id` per version

## Purpose

Captures full SCD Type 2 history of the product dimension. This is arguably the most
business-critical snapshot in the platform: product **price changes over time**, and
without SCD Type 2 history, historical revenue reporting would silently re-price past
orders at today's price instead of the price that was actually charged.

## Config

```yaml
snapshots:
  - name: dim_products
    relation: ref('eph_products')
    config:
      schema: gold
      database: walmart
      unique_key: product_id
      strategy: timestamp
      updated_at: product_updated_timestamp
      dbt_valid_to_current: "to_date('9999-12-31')"
```

## How it behaves

- **Source:** `eph_products` (ephemeral)
- **Change detection:** compares `product_updated_timestamp` against what's already
  snapshotted for that `product_id`
- **Current-row marker:** `dbt_valid_to = '9999-12-31'`

Note that `gold.fact_orders` already carries its own `unit_price`/`line_amount` at the
time of the transaction, independent of this snapshot — `dim_products.price` is for
"what does this product cost *now*" style reporting, not for recomputing historical
revenue, which the fact table's own measures already capture correctly.

## Columns

All columns from `eph_products` (see [`../ephemeral/eph_products.md`](../ephemeral/eph_products.md)),
plus dbt's snapshot metadata: `dbt_scd_id`, `dbt_updated_at`, `dbt_valid_from`,
`dbt_valid_to`.

## Consumed by

`gold.fact_orders` joins to this dimension by `product_id`.

## Related

- [`../ephemeral/eph_products.md`](../ephemeral/eph_products.md)
- [`../../../data-model/gold-layer.md`](../../../data-model/gold-layer.md)
