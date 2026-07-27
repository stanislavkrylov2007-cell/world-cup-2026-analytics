WITH unique_teams AS (
    SELECT home_team AS team_name FROM matches
    UNION
    SELECT away_team AS team_name FROM matches
)
SELECT
    (SELECT COUNT(*) FROM matches) AS match_count,
    (SELECT MIN(match_date) FROM matches) AS min_match_date,
    (SELECT MAX(match_date) FROM matches) AS max_match_date,
    (SELECT COUNT(*) FROM unique_teams) AS unique_team_count,
    (SELECT COUNT(DISTINCT tournament) FROM matches) AS tournament_count,
    (SELECT COUNT(DISTINCT country) FROM matches) AS country_count;
