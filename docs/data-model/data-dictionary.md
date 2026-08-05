# Data Dictionary

Column-level reference for every table in the platform, from raw source through gold.
For the *why* behind the layering, see [`../architecture/medallion-layers.md`](../architecture/medallion-layers.md).

## Conventions used throughout

- `is_active` is a `CHAR(1)` flag (`'Y'` / `'N'`) present on every source entity.
- `created_timestamp` / `updated_timestamp` are source-system audit columns; every
  incremental silver model uses `updated_timestamp` as its change-detection watermark.
- `processed_at` (silver) / `*_processed_at` (gold ephemeral) / `*_gold_processed_at`
  record when a row was last (re)computed by dbt — not when the underlying business
  event happened.

## Raw layer — PostgreSQL `raw.*`

The first landing point for the six core CSV-derived entities, defined in
`walmart_dataset/ddl/walmart_schema.sql` and loaded by `walmart_dataset/load_data.py`.

### `raw.customers`

| Column | Type | Notes |
|---|---|---|
| `customer_id` | `BIGINT` | Primary key |
| `first_name` | `VARCHAR(100)` | |
| `last_name` | `VARCHAR(100)` | |
| `email` | `VARCHAR(255)` | |
| `phone` | `VARCHAR(50)` | |
| `city` | `VARCHAR(100)` | |
| `province` | `VARCHAR(100)` | |
| `country` | `VARCHAR(100)` | |
| `created_timestamp` | `TIMESTAMP` | |
| `updated_timestamp` | `TIMESTAMP` | Change-detection watermark downstream |
| `is_active` | `CHAR(1)` | `'Y'` / `'N'` |

### `raw.stores`

| Column | Type | Notes |
|---|---|---|
| `store_id` | `BIGINT` | Primary key |
| `store_name` | `VARCHAR(255)` | |
| `city` | `VARCHAR(100)` | |
| `province` | `VARCHAR(100)` | |
| `country` | `VARCHAR(100)` | |
| `created_timestamp` | `TIMESTAMP` | |
| `updated_timestamp` | `TIMESTAMP` | |
| `is_active` | `CHAR(1)` | |

### `raw.products`

| Column | Type | Notes |
|---|---|---|
| `product_id` | `BIGINT` | Primary key |
| `product_name` | `VARCHAR(255)` | |
| `category` | `VARCHAR(100)` | |
| `brand` | `VARCHAR(100)` | |
| `price` | `NUMERIC(10,2)` | |
| `created_timestamp` | `TIMESTAMP` | |
| `updated_timestamp` | `TIMESTAMP` | |
| `is_active` | `CHAR(1)` | |

### `raw.employees`

| Column | Type | Notes |
|---|---|---|
| `employee_id` | `BIGINT` | Primary key |
| `store_id` | `BIGINT` | FK → `raw.stores.store_id` |
| `first_name` | `VARCHAR(100)` | |
| `last_name` | `VARCHAR(100)` | |
| `email` | `VARCHAR(255)` | |
| `job_title` | `VARCHAR(100)` | |
| `salary` | `NUMERIC(10,2)` | |
| `created_timestamp` | `TIMESTAMP` | |
| `updated_timestamp` | `TIMESTAMP` | |
| `is_active` | `CHAR(1)` | |

### `raw.orders`

| Column | Type | Notes |
|---|---|---|
| `order_id` | `BIGINT` | Primary key |
| `customer_id` | `BIGINT` | FK → `raw.customers.customer_id` |
| `store_id` | `BIGINT` | FK → `raw.stores.store_id` |
| `order_timestamp` | `TIMESTAMP` | When the order was placed |
| `payment_method` | `VARCHAR(50)` | |
| `order_status` | `VARCHAR(50)` | |
| `total_amount` | `NUMERIC(12,2)` | |
| `created_timestamp` | `TIMESTAMP` | |
| `updated_timestamp` | `TIMESTAMP` | |
| `is_active` | `CHAR(1)` | |

### `raw.order_items`

| Column | Type | Notes |
|---|---|---|
| `order_item_id` | `BIGINT` | Primary key |
| `order_id` | `BIGINT` | FK → `raw.orders.order_id` |
| `product_id` | `BIGINT` | FK → `raw.products.product_id` |
| `quantity` | `INT` | |
| `unit_price` | `NUMERIC(10,2)` | |
| `line_amount` | `NUMERIC(12,2)` | |
| `created_timestamp` | `TIMESTAMP` | |
| `updated_timestamp` | `TIMESTAMP` | |
| `is_active` | `CHAR(1)` | |

## Bronze layer — Databricks `walmart.bronze.*`

Mirrors the raw schema column-for-column for the six core entities (`customers`,
`stores`, `products`, `employees`, `orders`, `order_items`), declared as dbt sources in
`models/source/sources.yml`. Plus:

### `walmart.bronze.reviews`

Ingested independently via the S3 → Unity Catalog external location path (see
[`../setup/s3-integration.md`](../setup/s3-integration.md)). Not yet wired into the
`silver_t`/`gold` dbt pipeline — currently a standalone bronze Delta table.

## Silver layer

### `silver_t.*` — one table per core entity

Each is `SELECT *` from its bronze source plus one added column:

| Column | Notes |
|---|---|
| *(all bronze columns, unchanged)* | |
| `processed_at` | `current_timestamp()` at the time this row was (re)built |

Tables: `customers_t`, `employees_t`, `order_items_t`, `orders_t`, `products_t`, `stores_t`.

### `silver_b.obt_b` — the One Big Table

One row per `order_item`, every entity's columns present with an entity prefix to
avoid collisions:

| Prefix | Source | Key columns |
|---|---|---|
| `order_*` / unprefixed order columns | `orders_t` (alias `o`) | `order_id`, `store_id`, `order_timestamp`, `payment_method`, `order_status`, `total_amount` |
| `customer_*` | `customers_t` (alias `c`) | `customer_id`, `customer_first_name`, `customer_last_name`, `customer_email`, `customer_phone`, `customer_city`, `customer_province`, `customer_country` |
| unprefixed | `order_items_t` (alias `oi`) | `order_item_id`, `quantity`, `unit_price`, `line_amount` |
| `product_*` | `products_t` (alias `p`) | `product_id`, `product_name`, `category`, `brand`, `price` |
| `employee_*` | `employees_t` (alias `e`) | `employee_id`, `employee_first_name`, `employee_last_name`, `employee_email`, `job_title`, `salary` |
| `store_*` | `stores_t` (alias `s`) | `store_name`, `store_city`, `store_province`, `store_country` |

Each entity also contributes its own `*_created_timestamp`, `*_updated_timestamp`,
`*_is_active`, and `*_processed_at`, plus one platform-level `obt_b_processed_at`.

## Gold layer

### Ephemeral dimensions (`gold/ephemeral/eph_*`)

Each is a `SELECT DISTINCT` over one entity's columns from `obt_b`, adding
`<entity>_gold_processed_at`:

| Model | Grain / natural key | Columns |
|---|---|---|
| `eph_customers` | `customer_id` | customer attributes + `customer_gold_processed_at` |
| `eph_employees` | `employee_id` | employee attributes + `employee_gold_processed_at` |
| `eph_orders` | `order_id` (carries `order_item_id` as a bridge key) | order attributes + `order_gold_processed_at` |
| `eph_products` | `product_id` | product attributes + `product_gold_processed_at` |
| `eph_stores` | `store_id` | store attributes + `store_gold_processed_at` |

### Dimension snapshots (`gold.dim_*`)

Each `dim_*` snapshot wraps its `eph_*` model with dbt's standard SCD Type 2 metadata
columns, in addition to all the ephemeral model's own columns:

| Snapshot metadata column | Meaning |
|---|---|
| `dbt_scd_id` | Unique hash identifying this specific version of the row |
| `dbt_updated_at` | When dbt captured this version |
| `dbt_valid_from` | When this version became active |
| `dbt_valid_to` | When this version was superseded (`9999-12-31` if still current) |

### Fact table (`gold.fact_orders`)

| Column | Role |
|---|---|
| `order_id` | FK → `dim_orders` |
| `order_item_id` | Natural grain key |
| `product_id` | FK → `dim_products` |
| `store_id` | FK → `dim_stores` |
| `employee_id` | FK → `dim_employees` |
| `customer_id` | FK → `dim_customers` |
| `total_amount` | Measure — order-level total |
| `quantity` | Measure — line-item quantity |
| `unit_price` | Measure — line-item unit price |
| `line_amount` | Measure — line-item extended amount |

## See also

- [`entity-relationship-diagram.md`](entity-relationship-diagram.md) — visual ER diagrams for each layer
- [`bronze-layer.md`](bronze-layer.md), [`silver-layer.md`](silver-layer.md), [`gold-layer.md`](gold-layer.md)
- [`../dbt/models/`](../dbt/project-guide.md) — one document per model with full SQL-level detail
