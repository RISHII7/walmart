# dbt Project Guide

**Project root:** `walmart-dbt/walmart/` · **Profile:** `walmart` · **Adapter:** `dbt-databricks`

## Folder layout

```text
walmart-dbt/walmart/
├── dbt_project.yml       # project config: materializations, schemas per layer
├── profiles.yml          # Databricks connection (local only, gitignored)
├── models/
│   ├── source/           # sources.yml — bronze source declarations
│   ├── silver_t/         # one incremental model per core entity
│   ├── silver_b/         # obt_b — the One Big Table
│   └── gold/
│       ├── ephemeral/    # deduplicated dimension slices
│       └── fact/         # fact_orders
├── snapshots/             # SCD Type 2 dimension history (dim_*)
├── tests/                 # custom singular data tests
├── macros/                 # custom_schema.sql — schema-naming override
└── analyses/                # ad hoc / scratch SQL, not part of the DAG
```

## Materialization strategy (`dbt_project.yml`)

```yaml
models:
  walmart:
    silver_t:
      +materialized: table
      +schema: silver_t
    silver_b:
      +materialized: table
      +schema: silver_b
    gold:
      +materialized: table
      +schema: gold
      ephemeral:
        +materialized: ephemeral
```

Each layer gets its own Unity Catalog schema by folder convention — `silver_t`,
`silver_b`, `gold` — with `gold/ephemeral/*` overriding the parent folder's `table`
default down to `ephemeral`. Individual models still override further where needed
(every `silver_t` model sets `materialized='incremental'` in its own `config()` block,
which takes precedence over the folder-level `table` default).

## Schema naming

By default, dbt prefixes a model's custom `+schema` with the connection's target
schema (e.g. `dbt_schema_silver_t`). This project overrides that via a custom
`generate_schema_name` macro (`macros/custom_schema.sql`) so that a model's declared
schema is used exactly as-is:

```sql
{% macro generate_schema_name(custom_schema_name, node) -%}
    {%- set default_schema = target.schema -%}
    {%- if custom_schema_name is none -%}
        {{ default_schema }}
    {%- else -%}
        {{ custom_schema_name | trim }}
    {%- endif -%}
{%- endmacro %}
```

This keeps schema names predictable and matching the layer terminology
(`silver_t`, `silver_b`, `gold`) regardless of what target/profile is active.

## Sources

`models/source/sources.yml` declares the `walmart_databricks` source — catalog
`walmart`, schema `bronze` — covering all six core entity tables. Every silver model
reads from bronze exclusively through `{{ source(...) }}`, never a hardcoded table
name, which is what makes `dbt source freshness` meaningful as an independent
pipeline gate.

## Running the project

```bash
cd walmart-dbt/walmart

dbt debug                              # verify the Databricks connection
dbt source freshness                   # check bronze staleness
dbt run --select silver_t              # build the technical silver layer
dbt test --select silver_t
dbt run --select silver_b              # build the OBT
dbt test --select silver_b
dbt run --select gold/ephemeral        # compile the ephemeral dimensions
dbt snapshot                           # capture SCD Type 2 history
dbt run --select gold/fact             # build the fact table
```

This is exactly the sequence the Airflow DAG automates — see
[`../airflow/dag-reference.md`](../airflow/dag-reference.md).

## Full-refresh caveat

Because every `silver_t` model is incremental, changing filter logic on an existing
model (for example, adding an `is_active = 'Y'` predicate) only affects rows loaded
*after* the change. Applying new logic retroactively requires:

```bash
dbt run --select customers_t employees_t order_items_t orders_t products_t stores_t --full-refresh
```

## Related

- [`lineage.md`](lineage.md) — full model dependency graph
- [`testing-strategy.md`](testing-strategy.md) — every test in the project, and why
- [`models/`](models/) — one document per model
- [`../data-model/`](../data-model/data-dictionary.md) — column-level reference
