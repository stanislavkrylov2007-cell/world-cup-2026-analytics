SELECT
    COUNT(*) AS non_neutral_matches,
    SUM(CASE WHEN home_score > away_score THEN 1 ELSE 0 END) AS home_wins,
    SUM(CASE WHEN home_score = away_score THEN 1 ELSE 0 END) AS draws,
    SUM(CASE WHEN home_score < away_score THEN 1 ELSE 0 END) AS away_wins,
    ROUND(
        SUM(CASE WHEN home_score > away_score THEN 1 ELSE 0 END)::NUMERIC
        / NULLIF(COUNT(*), 0),
        4
    ) AS home_win_share,
    ROUND(
        SUM(CASE WHEN home_score = away_score THEN 1 ELSE 0 END)::NUMERIC
        / NULLIF(COUNT(*), 0),
        4
    ) AS draw_share,
    ROUND(
        SUM(CASE WHEN home_score < away_score THEN 1 ELSE 0 END)::NUMERIC
        / NULLIF(COUNT(*), 0),
        4
    ) AS away_win_share
FROM matches
WHERE neutral IS FALSE;
