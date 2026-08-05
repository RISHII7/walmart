# walmart (dbt project)

Transforms the Databricks bronze layer through silver into a conformed gold star
schema. Targets a Databricks SQL Warehouse via the `dbt-databricks` adapter.

Full documentation lives at [`../../docs/dbt/`](../../docs/dbt/project-guide.md) —
this file is just the local quick reference.

## Layers

| Path | Schema | What it builds |
|---|---|---|
| `models/source/` | — | Bronze source declarations (`sources.yml`) |
| `models/silver_t/` | `silver_t` | One incremental model per core entity |
| `models/silver_b/` | `silver_b` | `obt_b` — the One Big Table |
| `models/gold/ephemeral/` | (ephemeral, not persisted) | Deduplicated dimension slices |
| `snapshots/` | `gold` | SCD Type 2 dimension history (`dim_*`) |
| `models/gold/fact/` | `gold` | `fact_orders` |

## Commands

```bash
dbt debug                    # verify the Databricks connection
dbt source freshness         # check bronze staleness
dbt run --select silver_t
dbt test --select silver_t
dbt run --select silver_b
dbt test --select silver_b
dbt run --select gold/ephemeral
dbt snapshot
dbt run --select gold/fact
```

## Full documentation

- [`../../docs/dbt/project-guide.md`](../../docs/dbt/project-guide.md)
- [`../../docs/dbt/lineage.md`](../../docs/dbt/lineage.md)
- [`../../docs/dbt/testing-strategy.md`](../../docs/dbt/testing-strategy.md)
- [`../../docs/dbt/models/`](../../docs/dbt/models/) — one document per model
- [`../../docs/data-model/data-dictionary.md`](../../docs/data-model/data-dictionary.md)
