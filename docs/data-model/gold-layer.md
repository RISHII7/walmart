# Gold Layer Reference

**Schema:** `gold` (plus `ephemeral` sub-path, compiled inline) · **Engine:** Databricks, built by dbt

## Ephemeral dimensions

`models/gold/ephemeral/eph_{customers,employees,orders,products,stores}.sql` — each a
`SELECT DISTINCT` over one entity's columns from `silver_b.obt_b`, plus a
`<entity>_gold_processed_at` timestamp. Materialized as `materialized='ephemeral'` via
`dbt_project.yml`:

```yaml
models:
  walmart:
    gold:
      +materialized: table
      +schema: gold
      ephemeral:
        +materialized: ephemeral
```

Ephemeral models never persist as tables or views — dbt inlines their compiled SQL
directly into whatever references them (in this case, the corresponding snapshot).
They exist purely to deduplicate a repeating entity out of the OBT before it's
snapshotted.

**Why `eph_orders` is a little different:** unlike the other four, it also carries
`order_item_id` alongside the order-level columns, acting as a bridge key back to the
OBT's native order-item grain.

**Why there's no `eph_order_items`:** the OBT's grain already *is* order-item level —
running `DISTINCT` over order-item columns wouldn't deduplicate anything, since each
row is already unique at that grain. Order-item measures go straight into the fact
table instead.

## SCD Type 2 snapshots

`snapshots/dim_{customers,employees,orders,products,stores}.yml` — YAML-config
snapshots (dbt's newer declarative syntax, as opposed to the older Jinja
`{% snapshot %}` block form), one per ephemeral dimension:

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

Every snapshot uses the same shape: `strategy: timestamp` against the entity's own
`*_updated_timestamp` column, `unique_key` on the entity's natural key, and
`dbt_valid_to_current` set explicitly to `9999-12-31` — meaning "is this the current
version of the row" is always answerable with a plain date comparison
(`dbt_valid_to = '9999-12-31'`), never a `NULL` check, which keeps every downstream
query and BI tool's filter logic identical regardless of whether a row happens to be
current or historical.

### How a snapshot run behaves

1. dbt compares the current output of `eph_<entity>` against the latest snapshotted
   version of each row (by `unique_key`).
2. If a row is new, it's inserted with `dbt_valid_from` = now, `dbt_valid_to` =
   `9999-12-31`.
3. If a row's tracked columns changed since the last snapshot, dbt closes out the old
   version (`dbt_valid_to` = now) and inserts a new one.
4. If nothing changed, nothing happens — the row's existing version stays open.

This is why `dbt snapshot` is safe to run on every DAG execution: it's naturally
idempotent with respect to unchanged data.

## Fact table

`models/gold/fact/fact_orders.sql` — a single, deliberately thin `SELECT` off
`silver_b.obt_b`, carrying only foreign keys and measures:

```sql
SELECT
    order_id, order_item_id, product_id, store_id, employee_id, customer_id,
    total_amount, quantity, unit_price, line_amount
FROM {{ ref('obt_b') }}
```

`fact_orders` inherits the `gold` schema's default `+materialized: table` (no
per-model override needed) and sits at order-item grain, matching the OBT. Together
with the five `dim_*` snapshots, it forms a standard star schema — see
[`entity-relationship-diagram.md`](entity-relationship-diagram.md) for the visual.

## Related

- [`data-dictionary.md`](data-dictionary.md)
- [`silver-layer.md`](silver-layer.md) — what feeds into this layer
- [`../dbt/models/`](../dbt/project-guide.md) — per-model detail docs
