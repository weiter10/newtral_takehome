from datetime import datetime
from airflow import DAG
from airflow.decorators import task
from airflow.providers.apache.spark.operators.spark_submit import SparkSubmitOperator


@task.bash
def spark_submit(logical_date=None) -> str:
    date = logical_date.strftime('%Y-%m-%d')

    cmd = f"""
    /home/airflow/.local/lib/python3.10/site-packages/pyspark/bin/spark-submit \
    --master spark://spark-master:7077 \
    --deploy-mode client \
    --driver-cores 2 \
    --driver-memory 512m \
    --executor-memory 512m \
    --num-executors 1 \
    --executor-cores 2 \
    --total-executor-cores 2 \
    /opt/airflow/scripts/etl_job.py \
    --date {date}
    """
    return cmd


@task
def get_logical_date(logical_date=None) -> str:
    date = logical_date.strftime('%Y-%m-%d')
    print('---------------', type(logical_date), date)
    return date


with DAG(
    dag_id="etl_spark_media_monthly",
    start_date=datetime(2024, 8, 1),
    end_date=datetime(2024, 10, 1),
    schedule="@monthly",
    is_paused_upon_creation=True,
    max_active_runs=1,
):
    spark_job = SparkSubmitOperator(
        task_id='spark_submit',
        conn_id="spark_conn",
        driver_memory='1g',
        executor_memory='1g',
        executor_cores=8,
        num_executors=1,
        total_executor_cores=8,
        application='/opt/airflow/scripts/etl_job.py',
        application_args=[
            '--source', 'Media',
            '--date', get_logical_date(),
            '--recursive_month_level', 'True',
            '--warehouse_database', 'newtral',
            '--warehouse_table', 'media',
            ]
        )

    spark_job