# https://hub.docker.com/r/apache/airflow/tags
FROM apache/airflow:2.10.4-python3.10

COPY conf/connections.json /opt/airflow/connections.json

COPY conf/requirements.txt /requirements.txt
RUN pip install --upgrade pip
RUN pip install --no-cache-dir -r /requirements.txt

ENV SPARK_HOME=/home/airflow/.local/lib/python3.10/site-packages/pyspark

COPY conf/spark-defaults.conf $SPARK_HOME/conf/

#+----------------------------------+
#| Installing S3/MinIO dependencies |
#+----------------------------------+

RUN curl https://repo1.maven.org/maven2/org/apache/hadoop/hadoop-aws/3.3.4/hadoop-aws-3.3.4.jar \
    --output $SPARK_HOME/jars/hadoop-aws-3.3.4.jar

RUN curl https://repo1.maven.org/maven2/com/amazonaws/aws-java-sdk-bundle/1.12.262/aws-java-sdk-bundle-1.12.262.jar \
    --output $SPARK_HOME/jars/aws-java-sdk-bundle-1.12.262.jar

RUN curl https://jdbc.postgresql.org/download/postgresql-42.5.0.jar \
    --output $SPARK_HOME/jars/postgresql-42.5.0.jar

RUN curl https://repo1.maven.org/maven2/org/apache/iceberg/iceberg-spark-runtime-3.5_2.12/1.7.1/iceberg-spark-runtime-3.5_2.12-1.7.1.jar \
    --output $SPARK_HOME/jars/iceberg-spark-runtime-3.5_2.12-1.7.1.jar
#+--------------------------------------------------+
#| Downloading Hive Metastore 3.0.0 dependencies    |
#|                                                  |
#|   Obtained using these configurations:           |
#|                                                  |
#|    spark.sql.hive.metastore.jars=maven           |
#|    spark.sql.hive.metastore.version=3.0.0        |
#|                                                  |
#|   start a SparkSession with these configs        |
#|   and execute any spark.sql() command            |
#|                                                  |
#+--------------------------------------------------+

RUN mkdir -p ${SPARK_HOME}/hms-3.0.0/jars
COPY conf/hms-3.0.0-deps.txt ${SPARK_HOME}/hms-3.0.0/jars
RUN cd $SPARK_HOME/hms-3.0.0/jars && xargs -n1 -P1 curl --remote-name < hms-3.0.0-deps.txt


USER root

RUN apt-get update && \
    apt-get install -y wget

RUN apt-get install -y default-jre                                              && \
    echo "export JAVA_HOME=/usr/lib/jvm/java-17-openjdk-amd64" >> ~/.bashrc     && \
    echo "export PATH=\$JAVA_HOME/bin:\$PATH" >> ~/.bashrc
ENV JAVA_HOME /usr/lib/jvm/java-17-openjdk-amd64
ENV PATH "${JAVA_HOME}/bin:$PATH"

COPY conf/start.sh /start.sh
RUN chmod +x /start.sh
USER airflow
ENTRYPOINT ["/bin/bash","/start.sh"]