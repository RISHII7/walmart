# Model: `eph_stores`

**Layer:** gold/ephemeral · **Materialization:** ephemeral (compiled inline) · **Grain:** one row per `store_id`

## Purpose

Deduplicates the store entity back out of `silver_b.obt_b`, undoing the fan-out
caused by one store appearing across every order it fulfilled.

## SQL

```sql
SELECT DISTINCT
    store_id,
    store_name,
    store_city,
    store_province,
    store_country,
    store_created_timestamp,
    store_updated_timestamp,
    store_is_active,
    store_processed_at,
    CURRENT_TIMESTAMP() AS store_gold_processed_at
FROM {{ ref('obt_b') }}
```

## Materialization note

`ephemeral`: never persisted, inlined wherever referenced — only in
[`dim_stores`](../../../../walmart-dbt/walmart/snapshots/dim_stores.yml).

## Downstream consumers

- `gold.dim_stores` (snapshot, SCD Type 2)

## Related

- [`../../../data-model/gold-layer.md`](../../../data-model/gold-layer.md)
- [`../snapshots/dim_stores.md`](../snapshots/dim_stores.md)
