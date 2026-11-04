-- Re-runnable analytical views. Grain: one row per match in bi_match_facts,
-- one row per team and year in bi_team_year, one row per year in bi_year_trends.
CREATE OR REPLACE VIEW bi_match_facts AS
SELECT match_id, match_date AS date, EXTRACT(YEAR FROM match_date)::integer AS year,
       home_team, away_team, home_score, away_score, tournament, city, country,
       neutral, home_score + away_score AS total_goals,
       ABS(home_score - away_score) AS goal_difference,
       CASE WHEN home_score > away_score THEN 'Home win'
            WHEN home_score < away_score THEN 'Away win' ELSE 'Draw' END AS result
FROM matches;

CREATE OR REPLACE VIEW bi_team_year AS
WITH team_matches AS (
    SELECT year, home_team AS team, home_score AS goals_for,
           away_score AS goals_against FROM bi_match_facts
    UNION ALL
    SELECT year, away_team AS team, away_score AS goals_for,
           home_score AS goals_against FROM bi_match_facts
), aggregated AS (
    SELECT year, team, COUNT(*) AS matches,
           COUNT(*) FILTER (WHERE goals_for > goals_against) AS wins,
           COUNT(*) FILTER (WHERE goals_for = goals_against) AS draws,
           COUNT(*) FILTER (WHERE goals_for < goals_against) AS losses,
           SUM(goals_for) AS goals_for, SUM(goals_against) AS goals_against
    FROM team_matches GROUP BY year, team
)
SELECT *, ROUND(100.0 * wins / NULLIF(matches, 0), 2) AS win_rate_pct,
       DENSE_RANK() OVER (PARTITION BY year ORDER BY wins DESC, goals_for - goals_against DESC) AS year_rank
FROM aggregated;

CREATE OR REPLACE VIEW bi_year_trends AS
WITH yearly AS (
    SELECT year, COUNT(*) AS matches, ROUND(AVG(total_goals), 2) AS avg_goals,
           ROUND(100.0 * COUNT(*) FILTER (WHERE result = 'Draw') / NULLIF(COUNT(*), 0), 2) AS draw_share_pct,
           ROUND(100.0 * COUNT(*) FILTER (WHERE result = 'Home win' AND neutral IS FALSE)
                 / NULLIF(COUNT(*) FILTER (WHERE neutral IS FALSE), 0), 2) AS non_neutral_home_win_pct
    FROM bi_match_facts GROUP BY year
)
SELECT *, SUM(matches) OVER (ORDER BY year ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW)
          AS cumulative_matches
FROM yearly;
