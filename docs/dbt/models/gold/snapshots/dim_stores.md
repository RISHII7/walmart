# Snapshot: `dim_stores`

**Layer:** gold (snapshot) · **Strategy:** timestamp · **Schema:** `gold` · **Grain:** one row per `store_id` per version

## Purpose

Captures full SCD Type 2 history of the store dimension.

## Config

```yaml
snapshots:
  - name: dim_stores
    relation: ref('eph_stores')
    config:
      schema: gold
      database: walmart
      unique_key: store_id
      strategy: timestamp
      updated_at: store_updated_timestamp
      dbt_valid_to_current: "to_date('9999-12-31')"
```

## How it behaves

- **Source:** `eph_stores` (ephemeral)
- **Change detection:** compares `store_updated_timestamp` against what's already
  snapshotted for that `store_id`
- **Current-row marker:** `dbt_valid_to = '9999-12-31'`

## Columns

All columns from `eph_stores` (see [`../ephemeral/eph_stores.md`](../ephemeral/eph_stores.md)),
plus dbt's snapshot metadata: `dbt_scd_id`, `dbt_updated_at`, `dbt_valid_from`,
`dbt_valid_to`.

## Consumed by

`gold.fact_orders` joins to this dimension by `store_id`.

## Related

- [`../ephemeral/eph_stores.md`](../ephemeral/eph_stores.md)
- [`../../../data-model/gold-layer.md`](../../../data-model/gold-layer.md)
