FROM python:3.12-slim

ARG DBT_SNOWFLAKE_VERSION=1.12.0

RUN apt-get update \
    && apt-get install --yes --no-install-recommends git \
    && rm -rf /var/lib/apt/lists/*

RUN pip install --no-cache-dir \
    dbt-snowflake==${DBT_SNOWFLAKE_VERSION}

WORKDIR /usr/app/dbt

ENTRYPOINT ["dbt"]

