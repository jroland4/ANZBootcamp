# Databricks notebook source
# MAGIC %md
# MAGIC #### Setup

# COMMAND ----------

# MAGIC %scala
# MAGIC spark.conf.set("com.databricks.training.module_name", "Sensor_IoT")
# MAGIC val dbNamePrefix = {
# MAGIC   spark.conf.set("com.databricks.training.spark.dbName", "db_sensor_iot_db")
# MAGIC   spark.conf.set("com.databricks.training.spark.userName", "db")
# MAGIC }

# COMMAND ----------

databaseName = spark.conf.get("com.databricks.training.spark.dbName")
userName = spark.conf.get("com.databricks.training.spark.userName").replace('.', '_')
displayHTML("""User name is <b style="color:green">{}</b>.""".format(userName))

# COMMAND ----------

spark.sql("CREATE DATABASE IF NOT EXISTS {}".format(databaseName))
spark.sql("USE {}".format(databaseName))

displayHTML("""Using the database <b style="color:green">{}</b>.""".format(databaseName))

# COMMAND ----------

# Get the email address entered by the user on the calling notebook
db_name = spark.conf.get("com.databricks.training.spark.dbName")
 
# Get user name
 
#username = dbutils.notebook.entry_point.getDbutils().notebook().getContext().tags().apply('user')
#username_replaced = username.replace(".", "_").replace("@","_")
username = spark.conf.get("com.databricks.training.spark.userName").replace('.', '_')
#username = dbutils.widgets.get("user_name")
#base_table_path = f"{username}/deltademoasset/"
#local_data_path = f"{username}/deltademoasset/"

base_table_path = f"dbfs:/Users/{username}/deltademoasset"
local_data_path_native = f"/databricks/driver/{username}/deltademoasset"
local_data_path = f"file:/databricks/driver/{username}/deltademoasset"


# Construct the unique database name
database_name = db_name
print(f"Database Name: {database_name}")
 
# DBFS Path is
print(f"DBFS Path is: {base_table_path}")
 
#Local Data path is
print(f"Local Data Path is: {local_data_path}")

#checkpoint Streaming Path


spark.sql(f"DROP DATABASE IF EXISTS {database_name} CASCADE")
spark.sql(f"CREATE DATABASE IF NOT EXISTS {database_name}")
spark.sql(f"USE {database_name}")


# COMMAND ----------

import subprocess
 
#Delete local directories that may be present from a previous run 
process = subprocess.Popen(['rm', '-f', '-r', local_data_path],
                     stdout=subprocess.PIPE, 
                     stderr=subprocess.PIPE)
stdout, stderr = process.communicate()
 
stdout.decode('utf-8'), stderr.decode('utf-8')

# COMMAND ----------

process = subprocess.Popen(['mkdir', '-p', local_data_path],
                     stdout=subprocess.PIPE, 
                     stderr=subprocess.PIPE)
stdout, stderr = process.communicate()
 
stdout.decode('utf-8'), stderr.decode('utf-8')

# COMMAND ----------

# Copy the downloaded data to DBFS

import urllib.request
def makeLocal(dbFileName):
  dbfsPrefix = "file:"
  if dbFileName.startswith(dbfsPrefix):
        return dbFileName[len(dbfsPrefix):]
  else:
    raise Error(f"missing prefix on [{dbFileName}]")
def downloadSourceFile(local_name, url):
  dbfs_path = f"{base_table_path}/raw/{local_name}"
  local_path = f"{local_data_path}/{local_name}"
  print(f"#########################")
  print(f"Downloading [{local_name}] to [{local_path}]")
  urllib.request.urlretrieve(url, makeLocal(local_path))
  dbutils.fs.mv(local_path, dbfs_path)
downloadSourceFile("historical_sensor_data.csv", "https://www.dropbox.com/s/0dc8jqnw387zh1s/historical_sensor_data.csv?dl=1")
downloadSourceFile("backfill_sensor_data.csv", "https://www.dropbox.com/s/vf0s9hht1hwksj2/backfill_sensor_data.csv?dl=1")
downloadSourceFile("sensor_readings_current_labeled.csv", "https://www.dropbox.com/s/kvgcqaj51t4zwia/sensor_readings_current_labeled.csv?dl=1")
downloadSourceFile("plant_data.csv", "https://www.dropbox.com/s/t9yapifpy9l0a9z/plant_data.csv?dl=1")

# COMMAND ----------

dataPath1 = f"dbfs:/FileStore/{base_table_path}/plant_data.csv"

df1 = spark.read\
  .option("header", "true")\
  .option("delimiter", ",")\
  .option("inferSchema", "true")\
  .csv(dataPath1)

# display(df1)

# COMMAND ----------

df1.createOrReplaceTempView("plant_vw")

# COMMAND ----------

# MAGIC %fs rm -r dbfs:/user/hive/warehouse/db_sensor_iot_db.db/dim_plant

# COMMAND ----------

# MAGIC %sql
# MAGIC DROP TABLE IF EXISTS dim_plant;
# MAGIC 
# MAGIC CREATE TABLE dim_plant 
# MAGIC USING DELTA
# MAGIC AS (
# MAGIC   SELECT * FROM plant_vw
# MAGIC )

# COMMAND ----------

response = local_data_path + " " + base_table_path + " " + database_name

# COMMAND ----------

setup_responses=response.split()
dbfs_data_path = setup_responses[1]
database_name = setup_responses[2]
bronze_table_path = f"dbfs:/FileStore/{dbfs_data_path}tables/bronze"
silver_table_path = f"dbfs:/FileStore/{dbfs_data_path}tables/silver"
silver_clone_table_path = f"dbfs:/FileStore/{dbfs_data_path}tables/silver_clone"
silver_constraints_table_path = f"dbfs:/FileStore/{dbfs_data_path}tables/silver_constraints"
gold_table_path = f"dbfs:/FileStore/{dbfs_data_path}tables/gold"
parquet_table_path = f"dbfs:/FileStore/{dbfs_data_path}tables/parquet"
dbutils.fs.rm(bronze_table_path, recurse=True)
dbutils.fs.rm(silver_table_path, recurse=True)
dbutils.fs.rm(gold_table_path, recurse=True)
dbutils.fs.rm(parquet_table_path, recurse=True)
dbutils.fs.rm(silver_clone_table_path, recurse=True)

streaming_table_path = f"dbfs:/FileStore/{dbfs_data_path}tables/streaming"
output_sink_path = f"dbfs:/FileStore/{dbfs_data_path}tables/streaming_output"
checkpoint_stream1_path = f"dbfs:/FileStore/demo-{username}/deltademoasset/checkpoint_stream1/"

dbutils.fs.rm(streaming_table_path, recurse=True)
dbutils.fs.rm(checkpoint_stream1_path, recurse=True)
dbutils.fs.rm(output_sink_path, recurse=True)


print("DBFS path is {}".format(dbfs_data_path))
print("Database name is {}".format(database_name))
print("Brone Table Location is {}".format(bronze_table_path))
print("Silver Table Location is {}".format(silver_table_path))
print("Gold Table Location is {}".format(gold_table_path))
print("Parquet Table Location is {}".format(parquet_table_path))
print("Streaming Table Location is {}".format(streaming_table_path))
print("Checkpoint Location is {}".format(checkpoint_stream1_path))
print("Output Sink Location is {}".format(output_sink_path))

# COMMAND ----------

spark.sql(f"USE {database_name}")

# COMMAND ----------

# MAGIC %md
# MAGIC 
# MAGIC ## About the Data
# MAGIC 
# MAGIC The data used is mock data for 2 types of devices - Transformer/ Rectifier from 3 power plants generating 3 set of readings relevant to monitoring the status of that device type
# MAGIC 
# MAGIC ![ioT_Data](https://miro.medium.com/max/900/1*M_Q4XQ4pTCuANLyEZqrDOg.jpeg)

# COMMAND ----------

dataPath = f"dbfs:/FileStore/{dbfs_data_path}historical_sensor_data.csv"

df = spark.read\
  .option("header", "true")\
  .option("delimiter", ",")\
  .option("inferSchema", "true")\
  .csv(dataPath)

# display(df)

# COMMAND ----------

df.createOrReplaceTempView("bronze_readings_view")

# COMMAND ----------

# MAGIC %sql
# MAGIC -- select * from bronze_readings_view

# COMMAND ----------

# MAGIC %sql
# MAGIC -- select count(*) from bronze_readings_view

# COMMAND ----------

# MAGIC %sql
# MAGIC -- select distinct(device_operational_status) from bronze_readings_view

# COMMAND ----------

# MAGIC %md
# MAGIC ### Create Bronze Delta Lake Table

# COMMAND ----------

# MAGIC %sql
# MAGIC DROP TABLE IF EXISTS sensor_readings_historical_bronze;

# COMMAND ----------

spark.sql(f"CREATE TABLE IF NOT EXISTS sensor_readings_historical_bronze USING DELTA LOCATION '{bronze_table_path}' AS SELECT * from bronze_readings_view")

# COMMAND ----------

# MAGIC %md
# MAGIC ### Create Silver Table 
# MAGIC #### There is some missing data. Time to create a silver table, backfill and transform!

# COMMAND ----------

# MAGIC %sql
# MAGIC DROP TABLE IF EXISTS sensor_readings_historical_silver;

# COMMAND ----------

spark.sql(f"CREATE TABLE if not exists sensor_readings_historical_silver USING DELTA LOCATION '{silver_table_path}' AS SELECT * from bronze_readings_view")

# COMMAND ----------

dataPath = f"dbfs:/FileStore/{dbfs_data_path}backfill_sensor_data.csv"

df = spark.read\
  .option("header", "true")\
  .option("delimiter", ",")\
  .option("inferSchema", "true")\
  .csv(dataPath)

# display(df)

# COMMAND ----------

df.createOrReplaceTempView("backfill_view")

# COMMAND ----------

# MAGIC %sql
# MAGIC MERGE INTO sensor_readings_historical_silver AS SL
# MAGIC USING backfill_view AS BF
# MAGIC ON 
# MAGIC   SL.id = BF.id
# MAGIC WHEN MATCHED THEN 
# MAGIC UPDATE SET *
# MAGIC WHEN NOT MATCHED THEN 
# MAGIC INSERT *

# COMMAND ----------

# MAGIC %md
# MAGIC #### Using Lag & Lead to create an average value for bad readings

# COMMAND ----------

# MAGIC %sql
# MAGIC 
# MAGIC DROP TABLE IF EXISTS sensor_readings_historical_interpolations;
# MAGIC 
# MAGIC CREATE TABLE sensor_readings_historical_interpolations AS (
# MAGIC   WITH lags_and_leads AS (
# MAGIC     SELECT
# MAGIC       id, 
# MAGIC       reading_time,
# MAGIC       device_type,
# MAGIC       device_id,
# MAGIC       device_operational_status,
# MAGIC       reading_1,
# MAGIC       LAG(reading_1, 1, 0)  OVER (PARTITION BY device_id ORDER BY reading_time ASC, id ASC) AS reading_1_lag,
# MAGIC       LEAD(reading_1, 1, 0) OVER (PARTITION BY device_id ORDER BY reading_time ASC, id ASC) AS reading_1_lead,
# MAGIC       reading_2,
# MAGIC       LAG(reading_2, 1, 0)  OVER (PARTITION BY device_id ORDER BY reading_time ASC, id ASC) AS reading_2_lag,
# MAGIC       LEAD(reading_2, 1, 0) OVER (PARTITION BY device_id ORDER BY reading_time ASC, id ASC) AS reading_2_lead,
# MAGIC       reading_3,
# MAGIC       LAG(reading_3, 1, 0)  OVER (PARTITION BY device_id ORDER BY reading_time ASC, id ASC) AS reading_3_lag,
# MAGIC       LEAD(reading_3, 1, 0) OVER (PARTITION BY device_id ORDER BY reading_time ASC, id ASC) AS reading_3_lead
# MAGIC     FROM sensor_readings_historical_silver
# MAGIC   )
# MAGIC   SELECT 
# MAGIC     id,
# MAGIC     reading_time,
# MAGIC     device_type,
# MAGIC     device_id,
# MAGIC     device_operational_status,
# MAGIC     ((reading_1_lag + reading_1_lead) / 2) AS reading_1,
# MAGIC     ((reading_2_lag + reading_2_lead) / 2) AS reading_2,
# MAGIC     ((reading_3_lag + reading_3_lead) / 2) AS reading_3
# MAGIC   FROM lags_and_leads
# MAGIC   WHERE reading_1 = 999.99 OR reading_2 = 999.99 OR reading_3 = 999.99
# MAGIC   ORDER BY id ASC
# MAGIC )

# COMMAND ----------

# MAGIC %sql
# MAGIC MERGE INTO sensor_readings_historical_silver as SL
# MAGIC USING sensor_readings_historical_interpolations as INTP
# MAGIC ON
# MAGIC SL.id = INTP.id
# MAGIC WHEN MATCHED THEN
# MAGIC UPDATE SET SL.reading_1 = INTP.reading_1, SL.reading_2 = INTP.reading_2, SL.reading_3 = INTP.reading_3
# MAGIC WHEN NOT MATCHED THEN
# MAGIC INSERT *

# COMMAND ----------

# MAGIC %sql
# MAGIC DROP TABLE IF EXISTS sensor_readings_historical_silver_with_constraints

# COMMAND ----------

spark.sql(f"CREATE TABLE sensor_readings_historical_silver_with_constraints (id STRING, reading_time TIMESTAMP, device_type STRING, device_id STRING, device_operational_status STRING, reading_1 DOUBLE, reading_2 DOUBLE, reading_3 DOUBLE) USING DELTA LOCATION '{silver_constraints_table_path}'")

# COMMAND ----------

# MAGIC %sql
# MAGIC INSERT INTO sensor_readings_historical_silver_with_constraints SELECT * FROM bronze_readings_view WHERE reading_1 != 999.99 OR reading_2 != 999.99 OR reading_3 != 999.99

# COMMAND ----------

# MAGIC %sql
# MAGIC -- Attempting to run `DELETE` on the Delta table
# MAGIC DELETE FROM sensor_readings_historical_silver WHERE device_operational_status = 'CORRUPTED'

# COMMAND ----------

# MAGIC %sql
# MAGIC -- Attempting to run `UPDATE` on the Delta table
# MAGIC UPDATE sensor_readings_historical_silver SET `device_id` = '7G007T' WHERE device_id = '7G007TTTTT'

# COMMAND ----------

# MAGIC %sql
# MAGIC -- SELECT COUNT(*) FROM sensor_readings_historical_silver VERSION AS OF 1

# COMMAND ----------

spark.sql(f"CREATE TABLE IF NOT EXISTS sensor_readings_historical_silver_clone DEEP CLONE sensor_readings_historical_silver VERSION AS OF 1 LOCATION '{silver_clone_table_path}'")

# COMMAND ----------

# Generate new loans with dollar amounts 
tmp_df = sql("SELECT *, CAST(rand(10000)/8 AS double) AS reading_4, CAST(rand(1000)/9 AS double) AS reading_5 FROM sensor_readings_historical_silver LIMIT 10")
# display(tmp_df)

# COMMAND ----------

# Add the mergeSchema option
tmp_df.write.option("mergeSchema","true").format("delta").mode("append").save(silver_clone_table_path)

# COMMAND ----------

# MAGIC %sql
# MAGIC CREATE OR REPLACE TEMPORARY VIEW sensor_readings_historical_gold_view
# MAGIC AS
# MAGIC SELECT a.plant_id, a.device_id, a.plant_type, b.device_type, b.device_operational_status, b.reading_time, b.reading_1, b.reading_2, b.reading_3
# MAGIC FROM dim_plant a INNER JOIN sensor_readings_historical_silver b
# MAGIC ON a.device_id = b.device_id

# COMMAND ----------

# MAGIC %sql
# MAGIC CREATE TABLE sensor_readings_gold
# MAGIC USING delta
# MAGIC AS SELECT *
# MAGIC FROM sensor_readings_historical_gold_view

# COMMAND ----------

dataPath = f"dbfs:/FileStore/{base_table_path}sensor_readings_current_labeled.csv"

df = spark.read\
  .option("header", "true")\
  .option("delimiter", ",")\
  .option("inferSchema", "true")\
  .csv(dataPath)

# display(df)

# COMMAND ----------

df.createOrReplaceTempView("input_vw")

# COMMAND ----------

# MAGIC %sql
# MAGIC DROP TABLE IF EXISTS current_readings_labeled;
# MAGIC 
# MAGIC CREATE TABLE current_readings_labeled 
# MAGIC USING DELTA
# MAGIC AS (
# MAGIC   SELECT * FROM input_vw
# MAGIC )

# COMMAND ----------

# MAGIC %sql
# MAGIC DROP TABLE IF EXISTS current_readings_unlabeled;
# MAGIC 
# MAGIC CREATE TABLE current_readings_unlabeled 
# MAGIC USING DELTA
# MAGIC AS (
# MAGIC   SELECT 
# MAGIC     id,
# MAGIC     reading_time,
# MAGIC     device_type,
# MAGIC     device_id,
# MAGIC     reading_1,
# MAGIC     reading_2,
# MAGIC     reading_3
# MAGIC   FROM input_vw
# MAGIC )

# COMMAND ----------

dataPath = f"dbfs:/FileStore/{dbfs_data_path}/sensor_readings_current_labeled.csv"

df = spark.read\
  .option("header", "true")\
  .option("delimiter", ",")\
  .option("inferSchema", "true")\
  .csv(dataPath)
df.createOrReplaceTempView("streaming_vw")
spark.sql("DROP TABLE IF EXISTS readings_stream_source")
spark.sql("CREATE TABLE if not exists readings_stream_source (id INTEGER, reading_time TIMESTAMP, device_type STRING, device_id STRING, device_operational_status STRING, reading_1 DOUBLE, reading_2 DOUBLE, reading_3 DOUBLE) USING DELTA LOCATION '" + streaming_table_path + "'")
readings_stream = spark \
                   .readStream \
                   .format('delta') \
                   .table('readings_stream_source')

# Register the stream as a temporary view so we can run SQL on it
readings_stream.createOrReplaceTempView("readings_streaming")

# COMMAND ----------

dbutils.fs.mkdirs(checkpoint_stream1_path)
out_stream = spark.sql("""SELECT window, b.plant_id, b.plant_type, a.device_type, a.device_operational_status, count(a.device_type) count, avg(a.reading_1) average FROM readings_streaming a INNER JOIN dim_plant b GROUP BY WINDOW(a.reading_time, '2 minutes', '1 minute'), a.device_type, a.device_operational_status, b.plant_id, b.plant_type ORDER BY window DESC, a.device_type ASC LIMIT 10""")

swriter = out_stream.writeStream.format('delta').option('location', output_sink_path).option('checkpointLocation', checkpoint_stream1_path).outputMode('complete').table("readings_agg")

# COMMAND ----------

# Now let's simulate an application that streams data into our landing_point table

import time

next_row = 0

# Only loading 12 rows here
while(next_row < 120):
  
  time.sleep(1)

  next_row += 10
  
  spark.sql(f"""
    INSERT INTO readings_stream_source (
      SELECT * FROM current_readings_labeled
      WHERE id < {next_row} )
  """)

# COMMAND ----------

swriter.stop()
