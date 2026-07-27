WITH team_matches AS (
    SELECT
        home_team AS team,
        home_score AS goals_scored,
        away_score AS goals_allowed
    FROM matches

    UNION ALL

    SELECT
        away_team AS team,
        away_score AS goals_scored,
        home_score AS goals_allowed
    FROM matches
)
SELECT
    team,
    COUNT(*) AS matches,
    SUM(goals_scored) AS goals_scored,
    SUM(goals_allowed) AS goals_allowed,
    ROUND(AVG(goals_scored), 2) AS avg_goals_per_match
FROM team_matches
GROUP BY team
HAVING COUNT(*) >= 100
ORDER BY goals_scored DESC, team
LIMIT 20;
