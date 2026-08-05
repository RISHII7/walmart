# Medallion Layers, In Depth

## Bronze — `walmart.bronze.*`

Bronze is the landing layer inside Databricks Unity Catalog. It holds two kinds of
data, ingested two different ways:

1. **Core transactional entities** — `customers`, `stores`, `products`, `employees`,
   `orders`, `order_items` — six tables mirroring the operational schema.
2. **Supplementary feeds** — `reviews`, ingested independently via a file landed in
   Amazon S3 and pulled into a Delta table through a Databricks ingestion pipeline (see
   [`../setup/s3-integration.md`](../setup/s3-integration.md)).

Bronze tables carry the source schema close to as-is, plus lightweight audit columns
(`created_timestamp`, `updated_timestamp`, `is_active`) already present at the source.
No business logic, deduplication, or renaming happens here — that's intentional. If
bronze needed to change every time silver's logic changed, bronze would stop being a
reliable foundation.

## Silver — technical layer (`silver_t`) and business layer (`silver_b`)

### `silver_t`: one incremental model per entity

Every core entity gets its own dbt model (`customers_t`, `employees_t`,
`order_items_t`, `orders_t`, `products_t`, `stores_t`), each:

- materialized as an **incremental table**,
- keyed on the entity's natural primary key (`unique_key`),
- filtered forward only on rows where `updated_timestamp` is newer than what's
  already in the table (the `is_incremental()` watermark pattern),
- stamped with a `processed_at` column recording when the silver row was built.

This is where "did this row change since we last looked?" gets answered once, per
entity, instead of being re-derived by every downstream consumer.

### `silver_b`: the One Big Table

`obt_b` is a single dbt model that left-joins every `silver_t` table together around
`orders` as the anchor: customers (by `customer_id`), order_items (by `order_id`),
products (by `product_id`, joined through order_items), employees and stores (both by
`store_id`). The result is one wide, denormalized table where every row already carries
every attribute anyone downstream could need — no further joins required.

This exists so that the gold layer's job becomes purely about *reshaping*, not
*re-deriving relationships*. Every join in the system happens exactly once, in one
file, and gold-layer models only ever read from `obt_b`.

## Gold — conformed, business-facing layer

Gold is where `obt_b` gets split back apart into a proper analytical shape — a
dimensional model — rather than left as one flat table.

### Ephemeral dimension models

Five models (`eph_customers`, `eph_employees`, `eph_orders`, `eph_products`,
`eph_stores`) each run `SELECT DISTINCT` over their entity's columns straight from
`obt_b`. Because every one of these entities repeats across many `obt_b` rows (one
customer across many orders, one product across many order lines), `DISTINCT`
genuinely collapses duplication back into a clean one-row-per-entity shape — this is
the entire reason these models exist. They're materialized as `ephemeral`, meaning dbt
compiles them inline wherever they're referenced rather than persisting them as their
own table or view; they're a reusable snippet of SQL, not a destination.

There is deliberately **no** `eph_order_items` model: `obt_b`'s native grain already
*is* order-item level, so there's nothing to deduplicate there. Order-item attributes
flow straight into the fact table instead.

### Dimension snapshots — SCD Type 2

Each ephemeral dimension feeds a corresponding dbt **snapshot**
(`dim_customers`, `dim_employees`, `dim_orders`, `dim_products`, `dim_stores`), using
the `timestamp` strategy against each entity's own `updated_timestamp` column. Snapshots
give the platform full **Slowly Changing Dimension Type 2** history: every version of
every row is retained, each with a `dbt_valid_from`/`dbt_valid_to` window (current rows
get an explicit `9999-12-31` end date rather than `NULL`, so "is this row currently
active" is always a simple date comparison, never a null check).

### Fact table — `fact_orders`

`fact_orders` sits at order-item grain and carries only foreign keys (`order_id`,
`order_item_id`, `product_id`, `store_id`, `employee_id`, `customer_id`) and measures
(`total_amount`, `quantity`, `unit_price`, `line_amount`) — no descriptive attributes,
by design. Anyone querying gold joins this fact table to the `dim_*` snapshots to
recover descriptive context, which is exactly what makes point-in-time-correct
reporting possible: join to a dimension snapshot as of the fact's own timestamp, and
you get the dimension values that were true *then*, not just what's true today.

## Data quality

A singular dbt test (`test_obt`, warn severity) checks every row of `obt_b` for null
join keys — `order_id`, `product_id`, `employee_id`, `store_id`, `order_item_id`,
`customer_id` — which would indicate a broken join somewhere upstream. Column-level
tests (`not_null`, `unique`) are also declared on `products_t.product_id` and
`orders_t.order_id` in `models/silver_t/properties.yml`. See
[`../dbt/testing-strategy.md`](../dbt/testing-strategy.md) for the full picture.
