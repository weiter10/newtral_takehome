from datetime import datetime
from airflow.decorators import task
from airflow import models
from airflow.providers.common.sql.operators.sql import SQLExecuteQueryOperator

SCHEMA = "iceberg.newtral"
TABLE_MEDIA = "media"
TABLE_TIKTOKCOMMENT = 'tiktokcomment'


@task.bash
def create_airflow_user() -> str:

    cmd = "airflow users create --username airflow --password airflow --role Admin --firstname airflow --lastname airflow --email airflow@dummy.dummy"
    return cmd


@task.bash
def create_connections() -> str:

    cmd = "airflow connections import /opt/airflow/connections.json"
    return cmd


with models.DAG(
    dag_id="create_conns_and_raw_tables",
    schedule_interval='@once',
    start_date=datetime(2022, 1, 1),
    catchup=False,
    is_paused_upon_creation=False,
) as dag:

    trino_create_schema = SQLExecuteQueryOperator(
        task_id="trino_create_schema",
        conn_id='trino_conn',
        sql=f"CREATE SCHEMA IF NOT EXISTS {SCHEMA} WITH (location = 's3a://warehouse/')",
        handler=list,
    )

    create_table_media = SQLExecuteQueryOperator(
        task_id="create_table_media",
        conn_id='trino_conn',
        sql=f"""
            CREATE TABLE IF NOT EXISTS {SCHEMA}.{TABLE_MEDIA} (
            categories array(ROW(id varchar, name varchar)),
            date varchar,
            feed ROW(id varchar, name varchar),
            id varchar,
            link varchar,
            msgid varchar,
            sentiment varchar,
            source ROW(title varchar),
            summary varchar,
            text varchar,
            title varchar,
            type varchar,
            created_at_etl timestamp(6) with time zone,
            source_file_name varchar
            )
            WITH (
            format = 'PARQUET',
            format_version = 2,
            location = 's3a://warehouse/newtral.db/media'
            )
        """,
        handler=list,
    )

    create_table_tiktokcomment = SQLExecuteQueryOperator(
        task_id="create_table_tiktokcomment",
        conn_id='trino_conn',
        sql=f"""
            CREATE TABLE IF NOT EXISTS {SCHEMA}.{TABLE_TIKTOKCOMMENT} (
            categories array(ROW(id varchar, name varchar)),
            date varchar,
            feed ROW(id varchar, name varchar),
            id varchar,
            link varchar,
            msgid varchar,
            parentid varchar,
            sentiment varchar,
            text varchar,
            type varchar,
            user ROW(gender varchar, id varchar, username varchar),
            created_at_etl timestamp(6) with time zone,
            source_file_name varchar
            )
            WITH (
            format = 'PARQUET',
            format_version = 2,
            location = 's3a://warehouse/newtral.db/tiktokcomment'
            )
        """,
        handler=list,
    )

    (
        create_airflow_user(),
        create_connections()
        >> trino_create_schema
        >> [create_table_media, create_table_tiktokcomment]
    )
