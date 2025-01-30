from datetime import datetime
from airflow import DAG
from airflow.decorators import task
from airflow.providers.apache.spark.operators.spark_submit import SparkSubmitOperator


@task
def get_logical_date(logical_date=None) -> str:
    date = logical_date.strftime('%Y-%m-%d')
    print('---------------', type(logical_date), date)
    return date


with DAG(
    dag_id="etl_spark_tiktokcomment_daily",
    start_date=datetime(2024, 7, 31),
    end_date=datetime(2024, 8, 10),
    schedule_interval='0 1 * * *',
    is_paused_upon_creation=True,
    max_active_runs=1,
):
    spark_job = SparkSubmitOperator(
        task_id='spark_submit',
        conn_id="spark_conn",
        driver_memory='512m',
        executor_memory='512m',
        executor_cores=8,
        num_executors=1,
        total_executor_cores=8,
        application='/opt/airflow/scripts/etl_job.py',
        application_args=[
            '--source', 'TiktokComment',
            '--date', get_logical_date(),
            '--warehouse_database', 'newtral',
            '--warehouse_table', 'tiktokcomment',
            ]
        )

    spark_job
