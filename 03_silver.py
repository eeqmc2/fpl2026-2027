# Databricks notebook source
# MAGIC %sql
# MAGIC USE workspace.fpl;
# MAGIC
# MAGIC CREATE OR REPLACE TABLE silver_teams AS
# MAGIC SELECT id AS team_id, name AS team_name, short_name AS team_short, strength
# MAGIC FROM bronze_teams
# MAGIC WHERE snapshot_date = (SELECT MAX(snapshot_date) FROM bronze_teams);
# MAGIC
# MAGIC CREATE OR REPLACE TABLE silver_positions AS
# MAGIC SELECT id AS position_id, singular_name_short AS position
# MAGIC FROM bronze_positions
# MAGIC WHERE snapshot_date = (SELECT MAX(snapshot_date) FROM bronze_positions);
# MAGIC
# MAGIC CREATE OR REPLACE TABLE silver_gameweeks AS
# MAGIC SELECT id AS gw,
# MAGIC        from_utc_timestamp(to_timestamp(deadline_time), 'Australia/Sydney') AS deadline_sydney,
# MAGIC        finished, is_current, is_next,
# MAGIC        average_entry_score AS avg_score, highest_score
# MAGIC FROM bronze_gameweeks
# MAGIC WHERE snapshot_date = (SELECT MAX(snapshot_date) FROM bronze_gameweeks);

# COMMAND ----------

# MAGIC %sql
# MAGIC USE workspace.fpl;
# MAGIC
# MAGIC CREATE OR REPLACE TABLE silver_players AS
# MAGIC SELECT
# MAGIC   p.id                                        AS player_id,
# MAGIC   p.web_name                                  AS player,
# MAGIC   concat(p.first_name, ' ', p.second_name)    AS full_name,
# MAGIC   t.team_short                                AS team,
# MAGIC   pos.position,
# MAGIC   p.now_cost / 10.0                           AS price_m,
# MAGIC   p.total_points,
# MAGIC   p.minutes,
# MAGIC   CAST(p.form AS DOUBLE)                      AS form,
# MAGIC   CAST(p.points_per_game AS DOUBLE)           AS ppg,
# MAGIC   p.goals_scored, p.assists, p.clean_sheets, p.bonus,
# MAGIC   CAST(p.expected_goal_involvements AS DOUBLE) AS xgi,
# MAGIC   CAST(p.selected_by_percent AS DOUBLE)       AS selected_pct,
# MAGIC   p.status,
# MAGIC   p.chance_of_playing_next_round              AS chance_next,
# MAGIC   p.news,
# MAGIC   p.team                                      AS team_id,
# MAGIC   p.snapshot_date
# MAGIC FROM bronze_players p
# MAGIC JOIN silver_teams t      ON p.team = t.team_id
# MAGIC JOIN silver_positions pos ON p.element_type = pos.position_id
# MAGIC WHERE p.snapshot_date = (SELECT MAX(snapshot_date) FROM bronze_players);

# COMMAND ----------

# MAGIC %sql
# MAGIC USE workspace.fpl;
# MAGIC
# MAGIC CREATE OR REPLACE TABLE silver_player_snapshots AS
# MAGIC SELECT id AS player_id,
# MAGIC        snapshot_date,
# MAGIC        now_cost / 10.0                       AS price_m,
# MAGIC        total_points,
# MAGIC        CAST(form AS DOUBLE)                  AS form,
# MAGIC        CAST(selected_by_percent AS DOUBLE)   AS selected_pct
# MAGIC FROM bronze_players;

# COMMAND ----------

# MAGIC %sql
# MAGIC USE workspace.fpl;
# MAGIC
# MAGIC CREATE OR REPLACE TABLE silver_fixtures AS
# MAGIC SELECT f.id AS fixture_id,
# MAGIC        f.event AS gw,
# MAGIC        from_utc_timestamp(to_timestamp(f.kickoff_time), 'Australia/Sydney') AS kickoff_sydney,
# MAGIC        h.team_short AS home, a.team_short AS away,
# MAGIC        f.team_h_score AS home_goals, f.team_a_score AS away_goals,
# MAGIC        f.team_h_difficulty AS home_fdr, f.team_a_difficulty AS away_fdr,
# MAGIC        f.finished,
# MAGIC        f.team_h AS home_id, f.team_a AS away_id
# MAGIC FROM bronze_fixtures f
# MAGIC JOIN silver_teams h ON f.team_h = h.team_id
# MAGIC JOIN silver_teams a ON f.team_a = a.team_id
# MAGIC WHERE f.snapshot_date = (SELECT MAX(snapshot_date) FROM bronze_fixtures);
# MAGIC
# MAGIC CREATE OR REPLACE TABLE silver_team_fixtures AS
# MAGIC SELECT gw, fixture_id, kickoff_sydney, home_id AS team_id, home AS team,
# MAGIC        away AS opponent, 'H' AS venue, home_fdr AS fdr, finished
# MAGIC FROM silver_fixtures
# MAGIC UNION ALL
# MAGIC SELECT gw, fixture_id, kickoff_sydney, away_id, away,
# MAGIC        home, 'A', away_fdr, finished
# MAGIC FROM silver_fixtures;

# COMMAND ----------

# MAGIC %sql
# MAGIC USE workspace.fpl;
# MAGIC
# MAGIC SELECT COUNT(*)                                  AS players,
# MAGIC        COUNT_IF(team IS NULL OR position IS NULL) AS missing_lookups,
# MAGIC        COUNT(DISTINCT player_id) = COUNT(*)       AS ids_unique,
# MAGIC        MIN(price_m) AS min_price,
# MAGIC        MAX(price_m) AS max_price
# MAGIC FROM silver_players;

# COMMAND ----------

# MAGIC %sql
# MAGIC SELECT player, team, position, price_m, total_points, form, status
# MAGIC FROM workspace.fpl.silver_players
# MAGIC ORDER BY total_points DESC
# MAGIC LIMIT 10;