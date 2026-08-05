# S3 Integration

## Purpose

Amazon S3 backs a Unity Catalog **external location**, giving Databricks governed
access to data that lives outside the workspace's default managed storage. This
project uses it as the ingestion path for the supplementary `reviews` feed — data
that doesn't originate from the same operational Postgres/CDC path as the six core
entities.

## What's provisioned

- **S3 bucket:** `walmart-rishi`
- **Unity Catalog external location:** `walmart-rishi`, pointing at `s3://walmart-rishi`
- **IAM role:** a dedicated role (named `databricks-uc-<metastore-id>-walmart-rishi`)
  that Databricks assumes to read/write the bucket, scoped specifically to that
  purpose and tagged `DatabricksExternalBucket` for identification in AWS.

Provisioning an external location follows Databricks' standard Unity Catalog flow: an
AWS **storage credential** (the IAM role above) is created and granted trust to a
Databricks-controlled identity, then an **external location** object in Unity Catalog
is created referencing both the S3 path and that storage credential. Databricks
requests temporary, audited access to the AWS account to create and configure that
IAM role — visible and approvable directly in the AWS IAM console, with every action
attributable to a specific requestor identifier in AWS CloudTrail.

## Ingestion flow used for `reviews`

1. A source file was uploaded directly into the S3 bucket.
2. A Databricks data-ingestion job was created pointing at that file, through the
   external location.
3. That ingestion produced a managed Delta table, `walmart.bronze.reviews`.

This is a **separate ingestion path** from the six core entities (which flow from
PostgreSQL through a Databricks job triggered by the Airflow DAG's `ingest_cdc` task).
`reviews` is not currently declared as a dbt source or consumed by any `silver_t` /
`gold` model — it exists in bronze as a standalone table, ready to be wired into the
dbt pipeline the same way any other bronze source is (add it to
`models/source/sources.yml`, then build a `silver_t` model against it).

## Security note

Granting an external system (Databricks, in this case) IAM access to an AWS account
is a real, auditable trust decision — not something to click through reflexively.
Any future changes to this integration should be verified against the specific IAM
permissions being requested (visible via "View JSON" in the AWS approval screen)
before approval, the same way the original external-location grant was.

## Related

- [`databricks-unity-catalog-setup.md`](databricks-unity-catalog-setup.md)
- [`../data-model/bronze-layer.md`](../data-model/bronze-layer.md)
- [`../architecture/infrastructure.md`](../architecture/infrastructure.md)
