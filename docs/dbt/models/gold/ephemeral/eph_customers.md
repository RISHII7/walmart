# Model: `eph_customers`

**Layer:** gold/ephemeral · **Materialization:** ephemeral (compiled inline) · **Grain:** one row per `customer_id`

## Purpose

Deduplicates the customer entity back out of `silver_b.obt_b`, undoing the fan-out
caused by one customer having many orders.

## SQL

```sql
SELECT DISTINCT
    customer_id,
    customer_first_name,
    customer_last_name,
    customer_email,
    customer_phone,
    customer_city,
    customer_province,
    customer_country,
    customer_created_timestamp,
    customer_updated_timestamp,
    customer_is_active,
    customer_processed_at,
    CURRENT_TIMESTAMP() AS customer_gold_processed_at
FROM {{ ref('obt_b') }}
```

## Why `SELECT DISTINCT` works here

Every customer appears once per order in `obt_b`. `DISTINCT` over exactly the
customer's own columns (and nothing order-specific) collapses those repeats back down
to one row per `customer_id` — the entire reason this model exists.

## Materialization note

`ephemeral` means this model is never persisted as a table or view. dbt inlines its
compiled SQL as a CTE wherever it's referenced — in this case, only in
[`dim_customers`](../../../../walmart-dbt/walmart/snapshots/dim_customers.yml).

## Downstream consumers

- `gold.dim_customers` (snapshot, SCD Type 2)

## Related

- [`../../../data-model/gold-layer.md`](../../../data-model/gold-layer.md)
- [`../snapshots/dim_customers.md`](../snapshots/dim_customers.md)
