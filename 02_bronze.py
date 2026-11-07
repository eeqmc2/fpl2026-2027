# Databricks notebook source
from pyspark.sql import functions as F

RAW = "/Volumes/workspace/fpl/raw"

def add_tracking(df):
    return (df
        .withColumn("source_file", F.col("_metadata.file_path"))
        .withColumn("snapshot_date",
            F.to_date(F.regexp_extract("source_file", r"(\d{4}-\d{2}-\d{2})", 1)))
        .withColumn("ingested_at", F.current_timestamp()))

boot = add_tracking(
    spark.read.option("multiline", "true").json(f"{RAW}/bootstrap-static/"))

print("Snapshots found:", boot.select("snapshot_date").distinct().count())

# COMMAND ----------

def save_bronze(list_col, table):
    (boot
        .select("snapshot_date", "source_file", "ingested_at",
                F.explode(list_col).alias("r"))
        .select("snapshot_date", "source_file", "ingested_at", "r.*")
        .write.mode("overwrite")
        .option("overwriteSchema", "true")
        .saveAsTable(f"workspace.fpl.{table}"))
    print("saved", table)

for list_col, table in [("elements",      "bronze_players"),
                        ("teams",         "bronze_teams"),
                        ("events",        "bronze_gameweeks"),
                        ("element_types", "bronze_positions")]:
    save_bronze(list_col, table)

# COMMAND ----------

fx = add_tracking(
    spark.read.option("multiline", "true").json(f"{RAW}/fixtures/"))

(fx.write.mode("overwrite")
   .option("overwriteSchema", "true")
   .saveAsTable("workspace.fpl.bronze_fixtures"))
print("saved bronze_fixtures")

# COMMAND ----------

# MAGIC %sql
# MAGIC SELECT 'players' AS tbl, COUNT(*) AS n FROM workspace.fpl.bronze_players
# MAGIC UNION ALL SELECT 'teams',     COUNT(*) FROM workspace.fpl.bronze_teams
# MAGIC UNION ALL SELECT 'gameweeks', COUNT(*) FROM workspace.fpl.bronze_gameweeks
# MAGIC UNION ALL SELECT 'positions', COUNT(*) FROM workspace.fpl.bronze_positions
# MAGIC UNION ALL SELECT 'fixtures',  COUNT(*) FROM workspace.fpl.bronze_fixtures