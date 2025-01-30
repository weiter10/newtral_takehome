from pyspark.sql import SparkSession
from pyspark.sql import functions as F
import argparse

if __name__ == "__main__":

    parser = argparse.ArgumentParser(
        prog='ProgramName',
        description='What the program does',
        epilog='Text at the bottom of help')

    # Source 'directory' in AWS S3 bucket 'nwt-data-engineer': Media, TiktokComment
    parser.add_argument('--source', type=str, required=True,)
    # Date to read data from AWS S3 bucket. Format YYYY-MM-DD
    parser.add_argument('--date', type=str, required=True)
    # Trino database: newtral
    parser.add_argument('--warehouse_database', type=str, required=True)
    # Trino table: media, tiktokcomment
    parser.add_argument('--warehouse_table', type=str, required=True)
    # When True, ETL will process the data of the entire month of 'date' argument
    parser.add_argument(
        '--recursive_month_level',
        type=bool,
        required=False)
    args = parser.parse_args()

    year: str = args.date.split('-')[0]
    month: str = args.date.split('-')[1]
    day: str = args.date.split('-')[2]

    if args.recursive_month_level is not None and args.recursive_month_level:
        # read json for entire month
        year = args.date.split('-')[0]
        month = args.date.split('-')[1]
        s3_input_path = f"s3a://nwt-data-engineer/{args.source}/{year}/{month}"
    else:
        # read just a day of json data
        s3_input_path = f"s3a://nwt-data-engineer/{args.source}/{year}/{month}/{day}/"

    print('************************* s3 input path', s3_input_path)

    # The default provider for the protocol s3a is MINIO (spark-defaults.conf)
    # It is needed put specific configuration for using AWS S3 bucket 'nwt-data-engineer'
    spark = SparkSession.builder \
        .appName("SparkSession-Iceberg") \
        .config("spark.dynamicAllocation.enabled", "false") \
        .config("spark.jars.packages", "org.apache.iceberg:iceberg-spark-runtime-3.5_2.12:1.7.1") \
        .config("spark.sql.extensions", "org.apache.iceberg.spark.extensions.IcebergSparkSessionExtensions") \
        .config("spark.sql.catalog.iceberg", "org.apache.iceberg.spark.SparkCatalog") \
        .config("spark.sql.catalog.iceberg.type", "hive") \
        .config("spark.sql.catalog.iceberg.uri", "thrift://hive-metastore:9083") \
        .config('spark.hadoop.fs.s3a.bucket.nwt-data-engineer.aws.credentials.provider',
                'org.apache.hadoop.fs.s3a.AnonymousAWSCredentialsProvider')\
        .config('spark.hadoop.fs.s3a.bucket.nwt-data-engineer.endpoint',
                's3.eu-west-1.amazonaws.com')\
        .getOrCreate()

    # Read S3 bucket
    if args.recursive_month_level is not None and args.recursive_month_level:
        df = spark.read.option(
            "recursiveFileLookup", "true").json(s3_input_path)
    else:
        df = spark.read.json(s3_input_path)

    # Added columns for lineage :)
    df = df\
        .withColumn('created_at_etl', F.current_timestamp())\
        .withColumn('source_file_name', F.input_file_name())

    # print(spark.sparkContext.getConf().getAll())
    # exit(0)

    # Remove duplicates from input data (if they exist)
    df.dropDuplicates(['id']).createOrReplaceTempView(
        'source_data_wo_duplicates')

    # Perform UPSERT. A new row will be inserted in target (trino) table
    # if its id doesn't exist in target yet
    query = f"""
        MERGE INTO iceberg.{args.warehouse_database}.{args.warehouse_table} t
        USING (SELECT * FROM source_data_wo_duplicates) s
        ON t.id = s.id
        WHEN NOT MATCHED THEN INSERT *
    """

    spark.sql(query).show()

    spark.stop()
    exit(0)
