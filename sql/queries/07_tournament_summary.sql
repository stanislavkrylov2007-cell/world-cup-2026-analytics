SELECT
    tournament,
    COUNT(*) AS match_count,
    MIN(match_date) AS first_match_date,
    MAX(match_date) AS last_match_date,
    ROUND(AVG(home_score + away_score), 2) AS avg_total_goals
FROM matches
GROUP BY tournament
HAVING COUNT(*) >= 50
ORDER BY match_count DESC, tournament
LIMIT 30;
