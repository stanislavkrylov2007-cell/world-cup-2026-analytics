SELECT
    match_date,
    home_team,
    away_team,
    home_score,
    away_score,
    tournament,
    city,
    country,
    GREATEST(home_score, away_score) AS max_side_score,
    home_score + away_score AS total_goals
FROM matches
WHERE home_score > 20 OR away_score > 20
ORDER BY max_side_score DESC, total_goals DESC, match_date;
