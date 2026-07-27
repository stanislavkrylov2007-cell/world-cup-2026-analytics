WITH team_matches AS (
    SELECT
        home_team AS team,
        home_score AS goals_for,
        away_score AS goals_against
    FROM matches

    UNION ALL

    SELECT
        away_team AS team,
        away_score AS goals_for,
        home_score AS goals_against
    FROM matches
)
SELECT
    team,
    COUNT(*) AS matches,
    SUM(goals_for) AS goals_for,
    SUM(goals_against) AS goals_against,
    ROUND(AVG(goals_for), 3) AS avg_goals_for,
    ROUND(AVG(goals_against), 3) AS avg_goals_against
FROM team_matches
GROUP BY team
HAVING COUNT(*) >= 100
ORDER BY avg_goals_for DESC, goals_for DESC, team
LIMIT 20;
