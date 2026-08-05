# walmart_dataset

The raw layer: source CSVs, the PostgreSQL DDL that gives them a typed schema, and
the script that loads one into the other.

Full documentation: [`../docs/setup/postgres-setup.md`](../docs/setup/postgres-setup.md),
[`../docs/data-model/data-dictionary.md`](../docs/data-model/data-dictionary.md).

## Contents

```text
walmart_dataset/
├── data/
│   ├── customers.csv
│   ├── stores.csv
│   ├── products.csv
│   ├── employees.csv
│   ├── orders.csv
│   └── order_items.csv
├── ddl/
│   └── walmart_schema.sql   # creates the `raw` schema and all six tables
└── load_data.py              # bulk-loads each CSV into its raw.* table via psycopg COPY
```

## Usage

```bash
# 1. Set POSTGRES_CONNECTION_STRING in a .env file at the repo root

# 2. Create the schema
psql "$POSTGRES_CONNECTION_STRING" -f ddl/walmart_schema.sql

# 3. Load the data
uv run python load_data.py
```

## Why this exists as a separate step

These six entities are the platform's operational source of truth before anything
reaches Databricks. Landing them in a strictly-typed Postgres schema first — rather
than loading straight into the lakehouse — means a malformed row or type mismatch
gets caught here, in a disposable environment, instead of silently propagating into
bronze.

## Related

- [`../docs/setup/postgres-setup.md`](../docs/setup/postgres-setup.md)
- [`../docs/data-model/data-dictionary.md`](../docs/data-model/data-dictionary.md#raw-layer--postgresql-raw)
- [`../docs/setup/local-development.md`](../docs/setup/local-development.md)
