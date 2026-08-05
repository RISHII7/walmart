# Bronze Layer Reference

**Catalog:** `walmart` · **Schema:** `bronze` · **Engine:** Databricks (Unity Catalog, Delta Lake)

## What lives here

| Table | Ingestion path | Grain |
|---|---|---|
| `customers` | Loaded from `raw.customers` (PostgreSQL) | one row per customer |
| `stores` | Loaded from `raw.stores` | one row per store |
| `products` | Loaded from `raw.products` | one row per product |
| `employees` | Loaded from `raw.employees` | one row per employee |
| `orders` | Loaded from `raw.orders` | one row per order |
| `order_items` | Loaded from `raw.order_items` | one row per order line item |
| `reviews` | Landed in S3, ingested via a Databricks ingestion pipeline | one row per review |

## Declaration

Bronze is declared to dbt as a **source**, not a model — dbt never builds these
tables, only reads from and tests them:

```yaml
# models/source/sources.yml
sources:
  - name: walmart_databricks
    database: walmart
    schema: bronze
    tables:
      - name: orders
      - name: customers
      - name: products
      - name: order_items
      - name: employees
      - name: stores
```

Every `silver_t` model references its source table via `{{ source('walmart_databricks',
'<table>') }}` rather than a hardcoded table name — this is what lets
`dbt source freshness` check bronze staleness independently of any model logic, and
what lets the whole schema/catalog be renamed or repointed in one place if it ever
needs to change.

## Design rules for this layer

- **No transformation.** Column names, types, and grain match the source system
  exactly. Anything that looks like cleanup belongs in `silver_t`, not here.
- **No deduplication.** If the source system produced duplicate rows, bronze has
  duplicate rows too — deduplication is `silver_t`'s job (by `unique_key` on each
  incremental model).
- **`reviews` is intentionally separate.** It arrived via a different path (S3 →
  Unity Catalog external location, not the Postgres → Databricks CDC path) and isn't
  yet declared as a dbt source or consumed by any downstream model. See
  [`../setup/s3-integration.md`](../setup/s3-integration.md) for how it got there.

## Related

- [`data-dictionary.md`](data-dictionary.md) — full column listing
- [`../setup/databricks-unity-catalog-setup.md`](../setup/databricks-unity-catalog-setup.md)
- [`../setup/s3-integration.md`](../setup/s3-integration.md)
