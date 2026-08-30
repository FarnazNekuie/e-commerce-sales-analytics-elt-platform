# Architecture Notes

## Data flow

1. **Source (Postgres)** — `postgres/init/01_create_tables.sql` defines the
   `olist` schema (customers, orders, order_items, products, sellers,
   payments, reviews, geolocation, product_category_translation), mirroring
   the Olist Brazilian e-commerce dataset. In production this schema lives
   on a Neon-hosted Postgres instance; `postgres/neon/01_configure_fivetran_user.sql`
   grants a dedicated read-only role (`fivetran_user`) the `SELECT` privileges
   Fivetran needs, including on future tables via `ALTER DEFAULT PRIVILEGES`.

2. **Extract & Load (Fivetran)** — A Fivetran Postgres connector replicates
   the `olist` schema into a raw schema in Snowflake. The connector itself is
   configured once in the Fivetran UI; this repo only automates *triggering
   and monitoring* an existing connection (see the DAG below), not initial
   connector setup.

3. **Orchestration (Airflow + Cosmos)** — `airflow/dags/olist_elt_pipeline.py`:
   - `trigger_fivetran_sync` snapshots the connector's current
     `succeeded_at`/`failed_at` timestamps, then calls Fivetran's
     `POST /connections/{id}/sync` endpoint. A `409 AlreadyInSync` response is
     treated as success (a sync is already running) rather than an error.
   - `wait_for_fivetran_sync` is an Airflow `@task.sensor` in `reschedule`
     mode that polls the connector every 15s (30 min timeout) until either
     `succeeded_at` or `failed_at` changes from the snapshot taken before the
     trigger — this is what correctly distinguishes "a sync just completed"
     from "a sync completed hours ago before this DAG run started."
   - Once the sync completes, a Cosmos `DbtTaskGroup` renders dbt models and tests as individual Airflow tasks rather than running one opaque shell command. This provides task-level execution status, retries, logs, and dependency visibility in the Airflow UI.

4. **Transform (dbt)** — Three-layer model structure under
   `dbt/olist_analytics/models/`:
   - `staging/` (views): 1:1 with raw source tables — renaming, trimming,
     and type/enum normalization only, no joins.
   - `intermediate/` (views): order-level aggregation of items, payments,
     and reviews (`int_*_aggregated`), then joined into `int_orders_enriched`
     and `int_products_enriched`/`int_order_items_enriched`.
   - `marts/` (tables): a conformed star schema (`dim_customers`,
     `dim_products`, `dim_sellers`, `fct_orders`, `fct_order_items`) plus
     three purpose-built reporting marts consumed directly by the dashboard:
     `mart_daily_sales`, `mart_customer_summary`,
     `mart_product_category_performance`.

5. **Serve (Looker Studio)** — The dashboard queries the marts layer
   directly; no data lives outside Snowflake except what Looker Studio caches
   for rendering.

## Data quality strategy

Quality is checked at two points, deliberately close to where each kind of
error is cheapest to catch:

- **At the source**, before replication: `postgres/validation/01_validate_source.sql`
  runs referential-integrity and range checks (orphaned foreign keys,
  out-of-range review scores, negative prices) directly against Postgres.
- **In the warehouse**, on every dbt run: schema tests (`not_null`, `unique`,
  `accepted_values`, `relationships`) attached to staging and mart models in
  `staging.yml` / `marts.yml`, plus one custom singular test,
  `tests/assert_order_payment_totals_reconcile.sql`, which fails the build if
  a mart's rolled-up payment total ever drifts from the sum of the
  underlying payment records.

## Local vs. production topology

Docker Compose only stands up the **orchestration** layer (Airflow) and a
**local** Postgres for development — it does not stand up Snowflake or
Fivetran, which are external managed services. Running `docker compose up`
gives you a working Airflow UI and scheduler; the DAG itself will only
succeed once `.env.fivetran` and `.env.dbt`/`profiles.yml` point at real
Fivetran and Snowflake accounts.
