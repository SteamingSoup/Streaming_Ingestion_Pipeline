# Streaming Ingestion Pipeline

## Prerequisites

1. [Docker](https://docs.docker.com/get-docker/) (make sure to have docker-compose as well)
2. [Postgresql](https://www.postgresql.org/)
3. [Conda](https://docs.conda.io/en/latest/)
3. [Kafka](https://kafka.apache.org/)

## Project
This projet is to develop a streaming ingestion pipeline that will utilize Kafka and Kafka connect. The production database will be running on Postgres and the goal will be to stream generated data to different sources. The data will be written to S3 for data lake ingestion and MySQL for a type of email service.

Kafka connect will be used to capture changes in a table from the Postgres database and write to a Kafka broker. Two connectors will write any changes from the Kafka broker to the S3 data lake and MySQL email service.

## Design
![Design](/images/System_diagram.png)

## Data
The data will be generated using a data generation script found in the [conda folder.](/conda)

## Setup and Run
### Creating Environment, Starting Database, and Generating Data
First a new environment will need to be created:
```
conda create -n kafka-pipeline python=3.7 -y
conda activate kafka-pipeline
```
Ensure all required packages are installed:
```
pip install -r packages.txt
```
Docker-compose can be used to start the Postgres database:
```
docker-compose -f docker-compose-pg.yml up -d
```
The Faker library is used in the data generation script to generate data that will insert records into the Postgres database.
```
python data_generation.py
```

### Starting Kafka Broker
It is time to setup a Kafka broker and begin a few other services. The Kafka broker will receive producer messages and store them, but this will also allow consumers to fetch messages. Kafka Connect will allow the connection of the postgres database and any other external systems. Kafdrop can be used as an easy to use opensource web UI to view Kafka topics and will help with debugging. Zookeeper will be used to help keep track of the status of Kafka cluster nodes. Schema registry will be used to help with compatability settings between services.

The above services can be started using:
```
docker-compose -f docker-compose-kafka.yml up -d
```
Logs can be viewed using:
```
docker-compose -f docker-compose-kafka.yml logs -f
```

### Source Connectors
Kafka Connect has two types of connectors: Source Connectors and Sink Connectors:
A source connector collects data from a system, such as databases, while a sink connector delivers data from Kafka topics into other systems.
The source connector will be configured to the Postgres database using the Kafka connect rest API:
```
curl -i -X PUT http://localhost:8083/connectors/SOURCE_POSTGRES/config \
     -H "Content-Type: application/json" \
     -d '{
            "connector.class":"io.confluent.connect.jdbc.JdbcSourceConnector",
            "connection.url":"jdbc:postgresql://postgres:5432/TEST",
            "connection.user":"TEST",
            "connection.password":"password",
            "poll.interval.ms":"1000",
            "mode":"incrementing",
            "incrementing.column.name":"index",
            "topic.prefix":"P_",
            "table.whitelist":"USERS",
            "validate.non.null":"false"
        }'
```
Once the connector is succesfully created a command stating that the connector was created should pop up. The configurations used above are now being sent to the Kafka Connect instance. An explaination for each configuration setting can be found [here.](https://docs.confluent.io/kafka-connect-jdbc/current/source-connector/source_config_options.html)

### Sink Connectors
Two sink connectors will need to be made for the MySQL service and S3 data lake.
First step is to get the MySQL database running:
```
docker-compose -f docker-compose-mysql.yml up -d
```
This will be configured using the following:
```
curl -i -X PUT http://localhost:8083/connectors/SINK_MYSQL/config \
     -H "Content-Type: application/json" \
     -d '{
               "connector.class":"io.confluent.connect.jdbc.JdbcSinkConnector",
               "tasks.max":1,
               "topics":"P_USERS",
           "insert.mode":"insert",
               "connection.url":"jdbc:mysql://mysql:3306/TEST",
               "connection.user":"TEST",
               "connection.password":"password",
               "auto.create":true
         }'
```
The generated data should now be streaming from the Postgres database to MySQL.

To write the data to the S3 data lake a few variables will need to be setup in the docker-compose-kafka.yml file. This includes AWS_ACCESS_KEY_ID and AWS_SECRET_KEY.
Once that is complete the S3 connector can be created with the following configurations:
```
curl -i -X PUT -H "Accept:application/json" \
    -H  "Content-Type:application/json" http://localhost:8083/connectors/SINK_S3/config \
    -d '
{
    "connector.class": "io.confluent.connect.s3.S3SinkConnector",
    "s3.region": "ap-southeast-1",
    "s3.bucket.name": "bucket-name",
    "topics": "P_USERS",
    "flush.size": "5",
    "timezone": "UTC",
    "tasks.max": "1",
    "value.converter.value.subject.name.strategy": "io.confluent.kafka.serializers.subject.RecordNameStrategy",
    "locale": "US",
    "format.class": "io.confluent.connect.s3.format.json.JsonFormat",
    "partitioner.class": "io.confluent.connect.storage.partitioner.DefaultPartitioner",
    "internal.value.converter": "org.apache.kafka.connect.json.JsonConverter",
    "storage.class": "io.confluent.connect.s3.storage.S3Storage",
    "rotate.schedule.interval.ms": "6000"
}'
```
And with this the generated data should now be streaming from the Postgres database to the S3 data lake and the pipeline is complete.
This pipeline should allow for near real-time data analytics capabilites. A benefit to such a pipeline is that Kafka and its components are horizontally scalable and more components to process real-time data can be added.

### Before you go
Docker images downloaded locally can be cleaned up by using:
```
docker system prune
```
And to shut down the docker containers running for this project:
```
docker stop $(docker ps -aq)
```
