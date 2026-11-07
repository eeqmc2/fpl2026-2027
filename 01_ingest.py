# Databricks notebook source
# MAGIC %sql
# MAGIC CREATE SCHEMA IF NOT EXISTS workspace.fpl;
# MAGIC CREATE VOLUME IF NOT EXISTS workspace.fpl.raw;

# COMMAND ----------

import requests, json, os, datetime

base = "https://fantasy.premierleague.com/api/"
today = datetime.date.today().isoformat()
headers = {"User-Agent": "Mozilla/5.0"}

for name in ["bootstrap-static", "fixtures"]:
    r = requests.get(base + name + "/", headers=headers, timeout=30)
    r.raise_for_status()
    folder = f"/Volumes/workspace/fpl/raw/{name}"
    os.makedirs(folder, exist_ok=True)
    with open(f"{folder}/{name}_{today}.json", "w") as f:
        json.dump(r.json(), f)
    print(name, "saved", len(r.content), "bytes")

# COMMAND ----------

df = spark.read.option("multiline", "true").json(
    "/Volumes/workspace/fpl/raw/bootstrap-static/")
display(df.selectExpr("explode(elements) as p")
          .select("p.web_name", "p.now_cost", "p.total_points")
          .orderBy("total_points", ascending=False).limit(10))