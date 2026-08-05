# Testing Strategy

## What's tested today

| Test | Type | Target | Severity | Purpose |
|---|---|---|---|---|
| `not_null` on `products_t.product_id` | generic (column) | `silver_t.products_t` | error | Primary key integrity |
| `unique` on `products_t.product_id` (where `price > 0`) | generic (column) | `silver_t.products_t` | error | No duplicate product rows among priced products |
| `not_null` on `orders_t.order_id` | generic (column) | `silver_t.orders_t` | error | Primary key integrity |
| `unique` on `orders_t.order_id` | generic (column) | `silver_t.orders_t` | error | No duplicate order rows |
| `test_obt` | singular | `silver_b.obt_b` | warn | Flags rows with a null join key |

Declared in `models/silver_t/properties.yml`:

```yaml
models:
  - name: products_t
    columns:
      - name: product_id
        data_tests:
          - not_null
          - unique:
              config:
                where: "price > 0"

  - name: orders_t
    columns:
      - name: order_id
        data_tests:
          - not_null
          - unique
```

And `tests/test_obt.sql` (a singular test — a standalone SQL file where any returned
row counts as a failure):

```sql
{{ config(severity='warn') }}

SELECT 1
FROM {{ ref('obt_b') }} AS obt
WHERE
    obt.order_id IS NULL
    OR obt.product_id IS NULL
    OR obt.employee_id IS NULL
    OR obt.store_id IS NULL
    OR obt.order_item_id IS NULL
    OR obt.customer_id IS NULL
```

## Why `warn` instead of `error` on the OBT test

`obt_b` uses `LEFT JOIN` throughout (see
[`../data-model/silver-layer.md`](../data-model/silver-layer.md)), so a null
`employee_id` or `store_id` on a given row isn't necessarily a bug — it can validly
mean "this order has no assigned employee yet." Making this test `warn`-severity means
it surfaces in `dbt test` output and CI logs without blocking the pipeline outright,
which matches its role as an early-warning signal rather than a hard data-quality gate.
The **key columns** (`not_null`/`unique` on `products_t.product_id` and
`orders_t.order_id`) are `error`-severity by contrast, because a duplicated or missing
primary key on a source entity is unambiguously a defect, not a legitimate business
state.

## Freshness checks

`dbt source freshness` runs against the bronze layer as its own Airflow task
(`source_freshness`), ahead of any model build — if bronze hasn't been refreshed
recently enough, the DAG surfaces that before wasting compute transforming stale data.

## Running tests

```bash
dbt test                       # everything
dbt test --select silver_t     # just the silver_t column tests
dbt test --select test_obt     # just the OBT null-key check
```

## Where this could grow

This is deliberately a starting test surface, not a ceiling. Natural next additions
would be `not_null`/`unique` tests on the remaining `silver_t` primary keys
(`customer_id`, `employee_id`, `store_id`, `order_item_id`), referential-integrity
tests between `order_items_t`/`orders_t`/`products_t`, and `accepted_values` checks on
enumerated columns like `order_status` and `payment_method`.

## Related

- [`project-guide.md`](project-guide.md)
- [`../data-model/silver-layer.md`](../data-model/silver-layer.md)
- [`../operations/runbook.md`](../operations/runbook.md) — what to do when a test fails
