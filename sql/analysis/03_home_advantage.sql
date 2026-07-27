SELECT
    CASE
        WHEN neutral IS TRUE THEN 'neutral'
        WHEN neutral IS FALSE THEN 'non_neutral'
        ELSE 'unknown'
    END AS venue_type,
    COUNT(*) AS match_count,
    SUM(CASE WHEN home_score > away_score THEN 1 ELSE 0 END) AS home_wins,
    SUM(CASE WHEN home_score = away_score THEN 1 ELSE 0 END) AS draws,
    SUM(CASE WHEN home_score < away_score THEN 1 ELSE 0 END) AS away_wins,
    ROUND(
        SUM(CASE WHEN home_score > away_score THEN 1 ELSE 0 END)::NUMERIC
        / NULLIF(COUNT(*), 0) * 100,
        2
    ) AS home_win_pct,
    ROUND(
        SUM(CASE WHEN home_score = away_score THEN 1 ELSE 0 END)::NUMERIC
        / NULLIF(COUNT(*), 0) * 100,
        2
    ) AS draw_pct,
    ROUND(
        SUM(CASE WHEN home_score < away_score THEN 1 ELSE 0 END)::NUMERIC
        / NULLIF(COUNT(*), 0) * 100,
        2
    ) AS away_win_pct
FROM matches
GROUP BY venue_type
ORDER BY venue_type;
