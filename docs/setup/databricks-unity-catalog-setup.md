# Databricks + Unity Catalog Setup

## What's provisioned

- A **Unity Catalog** metastore governing the `walmart` catalog, with `bronze`,
  `silver_t`, `silver_b`, and `gold` as schemas.
- A **SQL Warehouse**, used as the compute endpoint for both dbt and any ad hoc
  querying.
- An **external location** (`walmart-rishi`) backed by an S3 bucket, used for the
  supplementary `reviews` ingestion path — see
  [`s3-integration.md`](s3-integration.md) for the full detail on that piece
  specifically.

## dbt connection (`profiles.yml`)

```yaml
walmart:
  outputs:
    dev:
      type: databricks
      catalog: walmart
      host: <workspace-host>
      http_path: /sql/1.0/warehouses/<warehouse-id>
      schema: dbt_schema
      threads: 1
      token: <personal-access-token>
  target: dev
```

This file is **not committed** — it lives only in `~/.dbt/profiles.yml` locally (or,
during initial `dbt init` setup, a project-local copy that's gitignored) and carries
a real personal access token. See [`environment-variables.md`](environment-variables.md)
for the full list of secrets this project handles this way.

## Personal access token scope

Databricks personal access tokens inherit whatever entitlements the issuing user
account has. If dbt's connection test fails with something like *"provided access
token does not have required scopes: sql"*, the fix isn't regenerating the token —
it's confirming the account has the **Databricks SQL access** entitlement enabled
(workspace admin console → Users → the account → Entitlements), since a token can
never have more access than its owner does.

## Schema-per-layer convention

Rather than relying on dbt's default behavior of prefixing a custom `+schema` with
the target's own schema, this project declares a custom `generate_schema_name` macro
(`macros/custom_schema.sql`) so that `silver_t`, `silver_b`, and `gold` show up in
Unity Catalog exactly as named — no `dbt_schema_` prefix — keeping the catalog
browsable and matching the medallion terminology used everywhere else in the docs.
See [`../dbt/project-guide.md`](../dbt/project-guide.md#schema-naming).

## Verifying the connection

```bash
cd walmart-dbt/walmart
dbt debug
```

A healthy connection reports `Connection test: [OK connection ok]`.

## Related

- [`s3-integration.md`](s3-integration.md)
- [`../dbt/project-guide.md`](../dbt/project-guide.md)
- [`environment-variables.md`](environment-variables.md)
