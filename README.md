# Walmart Data Engineering

A small data engineering project around a synthetic Walmart retail dataset:
customers, stores, products, employees, orders, and order items.

## Layout

- `walmart_dataset/ddl/walmart_schema.sql` — Postgres DDL for the `raw` schema tables.
- `walmart_dataset/data/*.csv` — raw source data files.
- `walmart_dataset/load_data.py` — loads the CSVs into Postgres via `COPY`.
- `src/walmart/` — project package.

## Setup

```bash
uv sync
```

Create a `.env` file with:

```dotenv
POSTGRES_CONNECTION_STRING="postgresql://user:password@host:port/dbname?sslmode=require"
```

Apply the schema, then load the data:

```bash
psql "$POSTGRES_CONNECTION_STRING" -f walmart_dataset/ddl/walmart_schema.sql
cd walmart_dataset && uv run python load_data.py
```
