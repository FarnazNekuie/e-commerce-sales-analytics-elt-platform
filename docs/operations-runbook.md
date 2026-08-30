# Operations Runbook

This runbook describes how to start, validate, monitor, and troubleshoot the
Olist ELT platform.

## Pipeline overview

The `olist_elt_pipeline` DAG performs the following sequence:

1. Triggers the configured Fivetran connection.
2. Waits for the current Fivetran synchronization to finish.
3. Runs dbt models and tests through an Astronomer Cosmos `DbtTaskGroup`.
4. Publishes tested analytics marts in Snowflake for the Looker Studio
   dashboard.

The DAG is manually triggered because it uses `schedule=None`.

## Prerequisites

Before starting the platform, create the local configuration files described
in the README:

- `.env`
- `.env.airflow`
- `.env.dbt`
- `.env.fivetran`
- `dbt/olist_analytics/profiles.yml`
- `airflow/config/simple_auth_manager_passwords.json`

Never commit credentials, private keys, or generated environment files.

## Start the platform

Build and start the Docker Compose services:

```bash
docker compose up --build -d
```

Confirm that the services are running:

```bash
docker compose ps
```

Expected services include:

- `postgres`
- `airflow-db`
- `airflow-init`
- `airflow-api-server`
- `airflow-scheduler`
- `airflow-triggerer`
- `airflow-dag-processor`

The one-time `airflow-init` service may exit successfully after initialization.

## Validate the Airflow DAG

Check for DAG import errors:

```bash
docker compose exec airflow-scheduler \
  airflow dags list-import-errors
```

Confirm that the DAG is registered:

```bash
docker compose exec airflow-scheduler \
  airflow dags list
```

The DAG list should include:

```text
olist_elt_pipeline
```

## Run the pipeline

Open the Airflow UI at:

```text
http://localhost:8080
```

Sign in with the username configured in `docker-compose.yml` and the password
stored in the ignored Simple Auth Manager password file.

Locate `olist_elt_pipeline`, unpause it if necessary, and trigger a manual run.

## Monitor the pipeline

In the Airflow Grid or Graph view, confirm that the run progresses through:

1. Fivetran synchronization trigger
2. Fivetran synchronization sensor
3. Cosmos-generated dbt model and test tasks

The Fivetran sensor checks the connector every 15 seconds and times out after
30 minutes. A Fivetran `409 AlreadyInSync` response is accepted because it
means a synchronization is already running.

## View service logs

View scheduler logs:

```bash
docker compose logs --tail=200 airflow-scheduler
```

Follow scheduler logs:

```bash
docker compose logs -f airflow-scheduler
```

View API server logs:

```bash
docker compose logs --tail=200 airflow-api-server
```

View DAG processor logs:

```bash
docker compose logs --tail=200 airflow-dag-processor
```

View PostgreSQL source logs:

```bash
docker compose logs --tail=200 postgres
```

Press `Control-C` to stop following logs without stopping the containers.

## Validate dbt independently

Confirm that dbt can connect to Snowflake:

```bash
docker compose exec airflow-scheduler \
  /opt/airflow/dbt_venv/bin/dbt debug \
  --project-dir /opt/airflow/dbt/olist_analytics \
  --profiles-dir /opt/airflow/dbt/olist_analytics
```

Parse the dbt project:

```bash
docker compose exec airflow-scheduler \
  /opt/airflow/dbt_venv/bin/dbt parse \
  --project-dir /opt/airflow/dbt/olist_analytics \
  --profiles-dir /opt/airflow/dbt/olist_analytics
```

Run all models and tests:

```bash
docker compose exec airflow-scheduler \
  /opt/airflow/dbt_venv/bin/dbt build \
  --project-dir /opt/airflow/dbt/olist_analytics \
  --profiles-dir /opt/airflow/dbt/olist_analytics
```

List the Looker Studio exposure:

```bash
docker compose exec airflow-scheduler \
  /opt/airflow/dbt_venv/bin/dbt ls \
  --project-dir /opt/airflow/dbt/olist_analytics \
  --profiles-dir /opt/airflow/dbt/olist_analytics \
  --resource-type exposure
```

## Common failure scenarios

### Fivetran authentication failure

Symptoms:

- The trigger task receives an HTTP `401` or `403`.
- The DAG fails before the sensor starts.

Actions:

1. Confirm that `FIVETRAN_API_KEY` and `FIVETRAN_API_SECRET` are set in
   `.env.fivetran`.
2. Confirm that the credentials have access to the configured connection.
3. Restart the Airflow services after changing environment variables.

```bash
docker compose up -d --force-recreate
```

### Invalid Fivetran connection ID

Symptoms:

- The Fivetran API returns `404`.
- The connection cannot be retrieved or triggered.

Actions:

1. Verify `FIVETRAN_CONNECTION_ID` in `.env.fivetran`.
2. Confirm that the connection still exists in Fivetran.
3. Recreate the Airflow containers after correcting the value.

### Fivetran sensor timeout

Symptoms:

- `wait_for_fivetran_sync` runs for 30 minutes and then fails.

Actions:

1. Open the Fivetran connection and inspect its synchronization status.
2. Review connector logs for source or destination errors.
3. Confirm that Neon Postgres and Snowflake are reachable.
4. Fix the underlying connector problem before retrying the DAG.

### dbt connection failure

Symptoms:

- `dbt debug` cannot connect to Snowflake.
- Cosmos-generated dbt tasks fail before executing SQL.

Actions:

1. Verify the Snowflake variables in `.env.dbt`.
2. Confirm that `DBT_PRIVATE_KEY_HOST_PATH` points to the correct host file.
3. Confirm that the key is mounted read-only at
   `/keys/dbt_private_key.p8`.
4. Verify that the Snowflake user, role, warehouse, database, and schema exist.
5. Run `dbt debug` again before retrying the DAG.

### dbt model or test failure

Symptoms:

- One or more Cosmos tasks fail.
- `dbt build` reports model or data-test errors.

Actions:

1. Open the failed task log in Airflow.
2. Identify the failing model or test.
3. Run that resource independently with `dbt build --select`.
4. Correct the SQL, source data, or test expectation.
5. Run the complete `dbt build` before retrying the Airflow task.

Example:

```bash
docker compose exec airflow-scheduler \
  /opt/airflow/dbt_venv/bin/dbt build \
  --project-dir /opt/airflow/dbt/olist_analytics \
  --profiles-dir /opt/airflow/dbt/olist_analytics \
  --select mart_daily_sales
```

### DAG does not appear

Actions:

1. Run `airflow dags list-import-errors`.
2. Review `airflow-dag-processor` logs.
3. Compile the DAG locally:

```bash
python -m compileall -q airflow/dags
```

4. Confirm that `airflow/dags/olist_elt_pipeline.py` is mounted in the
   container.
5. Restart the DAG processor and scheduler if necessary:

```bash
docker compose restart airflow-dag-processor airflow-scheduler
```

### Dashboard data is outdated

Actions:

1. Confirm that the latest Fivetran synchronization succeeded.
2. Confirm that the latest Airflow DAG run completed successfully.
3. Run `dbt build` and verify that all models and tests pass.
4. Check the Snowflake mart tables directly.
5. Refresh the Looker Studio data source and verify its Snowflake credentials.
6. Confirm that dashboard controls are not filtering out the expected data.

## Stop the platform

Stop containers while preserving their data:

```bash
docker compose down
```

Do not add `--volumes` unless persistent PostgreSQL and Airflow metadata should
also be deleted.
