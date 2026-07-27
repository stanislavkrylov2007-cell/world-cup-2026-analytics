SELECT
    match_date,
    home_team,
    away_team,
    home_score,
    away_score,
    tournament,
    city,
    country
FROM matches
WHERE home_score > 20 OR away_score > 20
ORDER BY GREATEST(home_score, away_score) DESC, match_date;
