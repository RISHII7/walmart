# Silver Layer Reference

**Schemas:** `silver_t` (technical), `silver_b` (business) · **Engine:** Databricks, built by dbt

## `silver_t` — one incremental model per entity

| Model | Source | `unique_key` | Materialization |
|---|---|---|---|
| `customers_t` | `bronze.customers` | `customer_id` | incremental table |
| `employees_t` | `bronze.employees` | `employee_id` | incremental table |
| `order_items_t` | `bronze.order_items` | `order_item_id` | incremental table |
| `orders_t` | `bronze.orders` | `order_id` | incremental table |
| `products_t` | `bronze.products` | `product_id` | incremental table |
| `stores_t` | `bronze.stores` | `store_id` | incremental table |

Every model follows the same shape:

```sql
{{ config(materialized='incremental', unique_key='<entity>_id') }}

SELECT *, current_timestamp() AS processed_at
FROM {{ source('walmart_databricks', '<entity>') }}

{% if is_incremental() %}
WHERE updated_timestamp > (
    SELECT COALESCE(MAX(updated_timestamp), '1900-01-01') FROM {{ this }}
)
{% endif %}
```

The `is_incremental()` block is the whole mechanism: on the very first run (or a
`--full-refresh`), it's skipped entirely and every bronze row is loaded. On every
subsequent run, only rows whose `updated_timestamp` is newer than the max already
present get processed — everything else in the target table is left untouched.

**Consequence to remember:** changing a model's filter logic (for example, adding a
`WHERE is_active = 'Y'`) only changes what gets loaded *going forward*. Rows already
sitting in the table from before the change are not retroactively re-evaluated. The
only way to apply new logic to historical rows is `dbt run --select <model> --full-refresh`,
which drops and rebuilds the table from scratch.

## `silver_b` — the One Big Table

One model, `obt_b`, materialized as a table in the `silver_b` schema. It's built with a
Jinja-driven config list rather than hand-written joins — each entry in `configs`
describes one source table, its column projection (with aliasing), and its join
condition against the anchor (`orders`, aliased `o`):

```jinja
{% set configs = [
    {"table": "walmart.silver_t.orders_t", "columns": "...", "alias": "o"},
    {"table": "walmart.silver_t.customers_t", "columns": "...", "alias": "c",
     "join_condition": "o.customer_id = c.customer_id"},
    {"table": "walmart.silver_t.order_items_t", "columns": "...", "alias": "oi",
     "join_condition": "o.order_id = oi.order_id"},
    {"table": "walmart.silver_t.products_t", "columns": "...", "alias": "p",
     "join_condition": "oi.product_id = p.product_id"},
    {"table": "walmart.silver_t.employees_t", "columns": "...", "alias": "e",
     "join_condition": "o.store_id = e.store_id"},
    {"table": "walmart.silver_t.stores_t", "columns": "...", "alias": "s",
     "join_condition": "o.store_id = s.store_id"},
] %}
```

The generated SQL is a chain of `LEFT JOIN`s off `orders_t`, meaning the OBT's grain is
**order_item level**: every row is one order line item, carrying every attribute of its
order, customer, product, employee, and store alongside it. `LEFT JOIN` (rather than
`INNER JOIN`) means an order missing, say, an assigned employee still produces a row —
the employee columns are simply null for that row, rather than the whole order
disappearing from the OBT.

This config-driven approach means adding a new joined entity to the OBT is a matter of
adding one entry to `configs`, not restructuring the query by hand.

## Data quality on this layer

`test_obt` (in `tests/test_obt.sql`, `warn` severity) flags any `obt_b` row where
`order_id`, `product_id`, `employee_id`, `store_id`, `order_item_id`, or `customer_id`
is null — the signal that one of the joins above didn't find a match it should have.

## Related

- [`data-dictionary.md`](data-dictionary.md) — full column listing
- [`gold-layer.md`](gold-layer.md) — what's built on top of `obt_b`
- [`../dbt/testing-strategy.md`](../dbt/testing-strategy.md)
