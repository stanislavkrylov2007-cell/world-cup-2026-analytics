SELECT
    EXTRACT(YEAR FROM match_date)::INTEGER AS match_year,
    COUNT(*) AS match_count,
    ROUND(AVG(home_score + away_score), 2) AS avg_total_goals
FROM matches
GROUP BY match_year
ORDER BY match_year;
