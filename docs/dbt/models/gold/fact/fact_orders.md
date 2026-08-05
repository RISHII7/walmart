# Model: `fact_orders`

**Layer:** gold/fact · **Materialization:** table (inherited from `gold`'s folder default) · **Schema:** `gold` · **Grain:** one row per `order_item_id`

## Purpose

The single fact table in the star schema — deliberately thin, carrying only foreign
keys and measures, with every descriptive attribute pushed out to the `dim_*`
snapshots instead.

## SQL

```sql
SELECT
    order_id,
    order_item_id,
    product_id,
    store_id,
    employee_id,
    customer_id,
    total_amount,
    quantity,
    unit_price,
    line_amount
FROM {{ ref('obt_b') }}
```

## Why it's this thin

Every column here is either a foreign key into a `dim_*` snapshot or a numeric
measure. There's no `product_name`, no `customer_email` — anything descriptive lives
in a dimension and gets joined in at query time. This is standard star-schema
discipline: it keeps the fact table narrow (cheaper to scan, cheaper to store) and
means a dimension attribute only ever needs to change in one place.

## Columns

| Column | Role |
|---|---|
| `order_id` | FK → `dim_orders` |
| `order_item_id` | Grain key |
| `product_id` | FK → `dim_products` |
| `store_id` | FK → `dim_stores` |
| `employee_id` | FK → `dim_employees` |
| `customer_id` | FK → `dim_customers` |
| `total_amount` | Measure (order-level total, repeated across the order's line items) |
| `quantity` | Measure |
| `unit_price` | Measure |
| `line_amount` | Measure |

## Materialization

No per-model `config()` block — it inherits `+materialized: table` from the `gold`
folder default in `dbt_project.yml`, since nothing about this model needs the
`ephemeral` override that `gold/ephemeral/*` gets.

## Related

- [`../../../data-model/entity-relationship-diagram.md`](../../../data-model/entity-relationship-diagram.md) — the full star schema
- [`../../../data-model/gold-layer.md`](../../../data-model/gold-layer.md)
- [`../../lineage.md`](../../lineage.md)
