# PostgreSQL Setup (Raw Layer)

## Purpose

PostgreSQL holds the `raw` schema — the very first landing point for the six core
CSV-derived entities, and the place where source data is validated against a strict,
typed DDL before anything reaches the Databricks lakehouse.

## Schema

`walmart_dataset/ddl/walmart_schema.sql` creates a dedicated `raw` schema and all six
tables (`customers`, `stores`, `products`, `employees`, `orders`, `order_items`) with
explicit types and primary keys — see
[`../data-model/data-dictionary.md`](../data-model/data-dictionary.md#raw-layer--postgresql-raw) for the full column listing.

```bash
psql "$POSTGRES_CONNECTION_STRING" -f walmart_dataset/ddl/walmart_schema.sql
```

## Loading data

`walmart_dataset/load_data.py` streams each CSV in `walmart_dataset/data/` into its
corresponding `raw.*` table using `psycopg` 3's `COPY` API — chosen over row-by-row
inserts specifically because `COPY` is dramatically faster for bulk-loading flat
files, which is exactly what this script does on every run.

```python
import os
import psycopg
from dotenv import load_dotenv

load_dotenv()
conn_string = os.environ["POSTGRES_CONNECTION_STRING"]

csv_files = {
    "customers.csv": "raw.customers",
    "stores.csv": "raw.stores",
    "products.csv": "raw.products",
    "employees.csv": "raw.employees",
    "orders.csv": "raw.orders",
    "order_items.csv": "raw.order_items",
}
```

Connection details are read from `POSTGRES_CONNECTION_STRING`, loaded via
`python-dotenv` from a local `.env` file — never hardcoded, and the `.env` file itself
is gitignored.

Run it:

```bash
cd walmart_dataset
uv run python load_data.py
```

## `.env` contents expected

```dotenv
POSTGRES_CONNECTION_STRING="postgresql://user:password@host:port/dbname?sslmode=require"
```

## Why Postgres exists as a separate hop at all

It would be possible to load the source CSVs straight into Databricks bronze. Keeping
Postgres as an explicit intermediate layer means the CSVs are validated against a
strict, typed schema (catching malformed rows, wrong types, or constraint violations)
in a lightweight, disposable environment before that data is trusted enough to enter
the lakehouse — and it gives a clean, queryable staging point for verifying a new data
drop before promoting it further.

## Related

- [`../data-model/data-dictionary.md`](../data-model/data-dictionary.md)
- [`local-development.md`](local-development.md)
- [`environment-variables.md`](environment-variables.md)
