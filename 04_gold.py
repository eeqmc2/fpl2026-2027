# Databricks notebook source
# MAGIC %sql
# MAGIC USE workspace.fpl;
# MAGIC
# MAGIC CREATE OR REPLACE TABLE gold_player_value AS
# MAGIC SELECT player_id, player, team_id, team, position, price_m,
# MAGIC        total_points, minutes, form, ppg, selected_pct,
# MAGIC        ROUND(total_points / price_m, 2) AS pts_per_m,
# MAGIC        RANK() OVER (PARTITION BY position
# MAGIC                     ORDER BY total_points / price_m DESC) AS value_rank_in_pos
# MAGIC FROM silver_players
# MAGIC WHERE minutes >= 450      -- at least ~5 full games, to filter out flukes
# MAGIC   AND status = 'a';       -- available players only

# COMMAND ----------

# MAGIC %sql
# MAGIC USE workspace.fpl;
# MAGIC
# MAGIC CREATE OR REPLACE TABLE gold_team_next3 AS
# MAGIC WITH next_gw AS (
# MAGIC   SELECT MIN(gw) AS gw FROM silver_gameweeks WHERE is_next
# MAGIC )
# MAGIC SELECT tf.team_id,
# MAGIC        tf.team,
# MAGIC        COUNT(*)              AS fixtures_next3,
# MAGIC        ROUND(AVG(tf.fdr), 2) AS avg_fdr_next3,
# MAGIC        concat_ws(', ',
# MAGIC          transform(
# MAGIC            array_sort(collect_list(struct(tf.gw, tf.kickoff_sydney, tf.opponent, tf.venue))),
# MAGIC            x -> concat(x.opponent, '(', x.venue, ')'))) AS next3
# MAGIC FROM silver_team_fixtures tf
# MAGIC CROSS JOIN next_gw n
# MAGIC WHERE tf.gw BETWEEN n.gw AND n.gw + 2
# MAGIC GROUP BY tf.team_id, tf.team;

# COMMAND ----------

# MAGIC %sql
# MAGIC USE workspace.fpl;
# MAGIC
# MAGIC CREATE OR REPLACE TABLE gold_transfer_targets AS
# MAGIC SELECT v.player, v.team, v.position, v.price_m, v.form, v.pts_per_m,
# MAGIC        f.next3, f.fixtures_next3, f.avg_fdr_next3,
# MAGIC        ROUND(v.form * f.fixtures_next3 * (6 - f.avg_fdr_next3) / 3, 1) AS proj_pts_next3
# MAGIC FROM gold_player_value v
# MAGIC JOIN gold_team_next3 f ON v.team_id = f.team_id;

# COMMAND ----------

# MAGIC %sql
# MAGIC SELECT position, player, team, price_m, form, next3, avg_fdr_next3, proj_pts_next3
# MAGIC FROM (
# MAGIC   SELECT *, ROW_NUMBER() OVER (PARTITION BY position
# MAGIC                                ORDER BY proj_pts_next3 DESC) AS rn
# MAGIC   FROM workspace.fpl.gold_transfer_targets
# MAGIC )
# MAGIC WHERE rn <= 5
# MAGIC ORDER BY position, rn;