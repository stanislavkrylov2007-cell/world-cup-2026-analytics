SELECT
    match_date,
    home_team,
    away_team,
    home_score,
    away_score,
    ABS(home_score - away_score) AS goal_difference,
    CASE
        WHEN home_score > away_score THEN home_team
        ELSE away_team
    END AS winner,
    CASE
        WHEN home_score > away_score THEN away_team
        ELSE home_team
    END AS loser,
    CASE
        WHEN home_score > away_score THEN 'home'
        ELSE 'away'
    END AS winner_side,
    tournament
FROM matches
WHERE home_score <> away_score
ORDER BY goal_difference DESC, (home_score + away_score) DESC, match_date
LIMIT 20;
