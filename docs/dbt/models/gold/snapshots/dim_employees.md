# Snapshot: `dim_employees`

**Layer:** gold (snapshot) · **Strategy:** timestamp · **Schema:** `gold` · **Grain:** one row per `employee_id` per version

## Purpose

Captures full SCD Type 2 history of the employee dimension — job title and salary
changes, in particular, are exactly the kind of attribute change this exists to track.

## Config

```yaml
snapshots:
  - name: dim_employees
    relation: ref('eph_employees')
    config:
      schema: gold
      database: walmart
      unique_key: employee_id
      strategy: timestamp
      updated_at: employee_updated_timestamp
      dbt_valid_to_current: "to_date('9999-12-31')"
```

## How it behaves

- **Source:** `eph_employees` (ephemeral)
- **Change detection:** compares `employee_updated_timestamp` against what's already
  snapshotted for that `employee_id`
- **Current-row marker:** `dbt_valid_to = '9999-12-31'`

## Columns

All columns from `eph_employees` (see
[`../ephemeral/eph_employees.md`](../ephemeral/eph_employees.md)), plus dbt's snapshot
metadata: `dbt_scd_id`, `dbt_updated_at`, `dbt_valid_from`, `dbt_valid_to`.

## Consumed by

`gold.fact_orders` joins to this dimension by `employee_id`.

## Related

- [`../ephemeral/eph_employees.md`](../ephemeral/eph_employees.md)
- [`../../../data-model/gold-layer.md`](../../../data-model/gold-layer.md)
