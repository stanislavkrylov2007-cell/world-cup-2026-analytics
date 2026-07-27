SELECT
    match_date,
    CASE
        WHEN home_score > away_score THEN home_team
        ELSE away_team
    END AS winner,
    CASE
        WHEN home_score > away_score THEN away_team
        ELSE home_team
    END AS loser,
    CONCAT(home_score, ':', away_score) AS score,
    ABS(home_score - away_score) AS goal_difference,
    tournament
FROM matches
WHERE home_score <> away_score
ORDER BY goal_difference DESC, GREATEST(home_score, away_score) DESC, match_date
LIMIT 25;
