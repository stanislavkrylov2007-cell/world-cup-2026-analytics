WITH team_matches AS (
    SELECT
        match_date,
        home_team AS team,
        away_team AS opponent,
        home_score AS goals_for,
        away_score AS goals_against,
        CASE
            WHEN home_score > away_score THEN 'W'
            WHEN home_score = away_score THEN 'D'
            ELSE 'L'
        END AS result
    FROM matches

    UNION ALL

    SELECT
        match_date,
        away_team AS team,
        home_team AS opponent,
        away_score AS goals_for,
        home_score AS goals_against,
        CASE
            WHEN away_score > home_score THEN 'W'
            WHEN away_score = home_score THEN 'D'
            ELSE 'L'
        END AS result
    FROM matches
)
SELECT
    team,
    COUNT(*) AS matches,
    SUM(CASE WHEN result = 'W' THEN 1 ELSE 0 END) AS wins,
    SUM(CASE WHEN result = 'D' THEN 1 ELSE 0 END) AS draws,
    SUM(CASE WHEN result = 'L' THEN 1 ELSE 0 END) AS losses,
    SUM(goals_for) AS goals_for,
    SUM(goals_against) AS goals_against,
    SUM(goals_for) - SUM(goals_against) AS goal_difference,
    ROUND(
        SUM(CASE WHEN result = 'W' THEN 1 ELSE 0 END)::NUMERIC
        / NULLIF(COUNT(*), 0) * 100,
        2
    ) AS win_rate
FROM team_matches
GROUP BY team
ORDER BY wins DESC, win_rate DESC, goal_difference DESC, matches DESC, team
LIMIT 20;
