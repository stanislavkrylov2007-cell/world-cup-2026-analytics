SELECT
    tournament,
    COUNT(*) AS match_count,
    ROUND(AVG(home_score + away_score), 2) AS avg_total_goals,
    ROUND(AVG(ABS(home_score - away_score)), 2) AS avg_goal_difference
FROM matches
GROUP BY tournament
HAVING COUNT(*) >= 50
ORDER BY match_count DESC, tournament
LIMIT 20;
