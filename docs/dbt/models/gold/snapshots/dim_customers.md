# Snapshot: `dim_customers`

**Layer:** gold (snapshot) · **Strategy:** timestamp · **Schema:** `gold` · **Grain:** one row per `customer_id` per version

## Purpose

Captures full SCD Type 2 history of the customer dimension — every version of every
customer row, with explicit valid-from/valid-to windows.

## Config

```yaml
snapshots:
  - name: dim_customers
    relation: ref('eph_customers')
    config:
      schema: gold
      database: walmart
      unique_key: customer_id
      strategy: timestamp
      updated_at: customer_updated_timestamp
      dbt_valid_to_current: "to_date('9999-12-31')"
```

## How it behaves

- **Source:** `eph_customers` (ephemeral — compiled inline at snapshot time, not a
  persisted table)
- **Change detection:** compares `customer_updated_timestamp` against what's already
  snapshotted for that `customer_id`
- **Current-row marker:** `dbt_valid_to = '9999-12-31'` instead of `NULL` — every
  query that needs "is this row current" uses the same date comparison, current or
  historical, with no null-handling branch

## Columns

All columns from `eph_customers` (see
[`../ephemeral/eph_customers.md`](../ephemeral/eph_customers.md)), plus dbt's snapshot
metadata: `dbt_scd_id`, `dbt_updated_at`, `dbt_valid_from`, `dbt_valid_to`.

## Consumed by

`gold.fact_orders` joins to this dimension by `customer_id` for reporting; a
point-in-time-correct join additionally filters on
`dbt_valid_from <= <as-of> < dbt_valid_to`.

## Related

- [`../ephemeral/eph_customers.md`](../ephemeral/eph_customers.md)
- [`../../../data-model/gold-layer.md`](../../../data-model/gold-layer.md)
