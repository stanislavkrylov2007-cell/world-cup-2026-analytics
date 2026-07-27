WITH
oldest_match AS (
    SELECT
        match_date,
        home_team,
        away_team,
        home_score,
        away_score
    FROM matches
    ORDER BY match_date, match_id
    LIMIT 1
),
latest_match AS (
    SELECT
        match_date,
        home_team,
        away_team,
        home_score,
        away_score
    FROM matches
    ORDER BY match_date DESC, match_id DESC
    LIMIT 1
),
matches_by_year AS (
    SELECT
        EXTRACT(YEAR FROM match_date)::INTEGER AS match_year,
        COUNT(*) AS match_count,
        ROUND(AVG(home_score + away_score), 2) AS avg_total_goals
    FROM matches
    GROUP BY match_year
),
most_active_year AS (
    SELECT match_year, match_count
    FROM matches_by_year
    ORDER BY match_count DESC, match_year DESC
    LIMIT 1
),
highest_scoring_year AS (
    SELECT match_year, avg_total_goals, match_count
    FROM matches_by_year
    WHERE match_count >= 50
    ORDER BY avg_total_goals DESC, match_count DESC, match_year DESC
    LIMIT 1
),
top_tournament AS (
    SELECT tournament, COUNT(*) AS match_count
    FROM matches
    GROUP BY tournament
    ORDER BY match_count DESC, tournament
    LIMIT 1
),
top_host_country AS (
    SELECT country, COUNT(*) AS match_count
    FROM matches
    WHERE country IS NOT NULL
    GROUP BY country
    ORDER BY match_count DESC, country
    LIMIT 1
),
top_city AS (
    SELECT city, COUNT(*) AS match_count
    FROM matches
    WHERE city IS NOT NULL
    GROUP BY city
    ORDER BY match_count DESC, city
    LIMIT 1
),
biggest_home_win AS (
    SELECT
        match_date,
        home_team,
        away_team,
        home_score,
        away_score,
        home_score - away_score AS goal_difference
    FROM matches
    WHERE home_score > away_score
    ORDER BY goal_difference DESC, home_score DESC, match_date
    LIMIT 1
),
biggest_away_win AS (
    SELECT
        match_date,
        home_team,
        away_team,
        home_score,
        away_score,
        away_score - home_score AS goal_difference
    FROM matches
    WHERE away_score > home_score
    ORDER BY goal_difference DESC, away_score DESC, match_date
    LIMIT 1
),
highest_total_goals_match AS (
    SELECT
        match_date,
        home_team,
        away_team,
        home_score,
        away_score,
        home_score + away_score AS total_goals
    FROM matches
    ORDER BY total_goals DESC, GREATEST(home_score, away_score) DESC, match_date
    LIMIT 1
),
most_common_scoreline AS (
    SELECT
        CONCAT(home_score, ':', away_score) AS scoreline,
        COUNT(*) AS match_count
    FROM matches
    GROUP BY scoreline
    ORDER BY match_count DESC, scoreline
    LIMIT 1
)
SELECT
    'Oldest recorded match' AS fact_name,
    TO_CHAR(match_date, 'YYYY-MM-DD') AS fact_value,
    home_team || ' ' || home_score || ':' || away_score || ' ' || away_team AS details
FROM oldest_match

UNION ALL

SELECT
    'Most recent recorded match',
    TO_CHAR(match_date, 'YYYY-MM-DD'),
    home_team || ' ' || home_score || ':' || away_score || ' ' || away_team
FROM latest_match

UNION ALL

SELECT
    'Most active year',
    match_year::TEXT,
    match_count || ' matches'
FROM most_active_year

UNION ALL

SELECT
    'Highest-scoring year (50+ matches)',
    match_year::TEXT,
    avg_total_goals || ' goals per match across ' || match_count || ' matches'
FROM highest_scoring_year

UNION ALL

SELECT
    'Tournament with most matches',
    tournament,
    match_count || ' matches'
FROM top_tournament

UNION ALL

SELECT
    'Country hosting the most matches',
    country,
    match_count || ' matches'
FROM top_host_country

UNION ALL

SELECT
    'Most frequent host city',
    city,
    match_count || ' matches'
FROM top_city

UNION ALL

SELECT
    'Biggest home win',
    goal_difference::TEXT || '-goal margin',
    TO_CHAR(match_date, 'YYYY-MM-DD') || ': ' || home_team || ' ' || home_score || ':' || away_score || ' ' || away_team
FROM biggest_home_win

UNION ALL

SELECT
    'Biggest away win',
    goal_difference::TEXT || '-goal margin',
    TO_CHAR(match_date, 'YYYY-MM-DD') || ': ' || home_team || ' ' || home_score || ':' || away_score || ' ' || away_team
FROM biggest_away_win

UNION ALL

SELECT
    'Highest-scoring single match',
    total_goals::TEXT || ' total goals',
    TO_CHAR(match_date, 'YYYY-MM-DD') || ': ' || home_team || ' ' || home_score || ':' || away_score || ' ' || away_team
FROM highest_total_goals_match

UNION ALL

SELECT
    'Most common scoreline',
    scoreline,
    match_count || ' matches'
FROM most_common_scoreline;
