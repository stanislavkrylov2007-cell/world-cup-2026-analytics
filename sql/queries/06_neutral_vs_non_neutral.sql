SELECT
    CASE
        WHEN neutral IS TRUE THEN 'true'
        WHEN neutral IS FALSE THEN 'false'
        ELSE 'null'
    END AS neutral_status,
    COUNT(*) AS match_count,
    ROUND(AVG(home_score + away_score), 2) AS avg_total_goals,
    ROUND(
        AVG(CASE WHEN home_score = away_score THEN 1.0 ELSE 0.0 END),
        4
    ) AS draw_share,
    ROUND(
        AVG(CASE WHEN home_score > away_score THEN 1.0 ELSE 0.0 END),
        4
    ) AS home_win_share
FROM matches
GROUP BY neutral_status
ORDER BY neutral_status;
