-- Run only in a disposable database: psql -v ON_ERROR_STOP=1 -f tests/bi_marts_assertions.sql
BEGIN;
CREATE SCHEMA bi_test;
SET LOCAL search_path TO bi_test;
\ir ../sql/ddl/001_create_matches.sql
INSERT INTO matches (match_date, home_team, away_team, home_score, away_score, tournament, neutral, source_file)
VALUES ('2023-01-01', 'A', 'B', 2, 0, 'Cup', FALSE, 'fixture'),
       ('2023-02-01', 'B', 'A', 1, 1, 'Cup', TRUE, 'fixture'),
       ('2024-01-01', 'A', 'B', 0, 0, 'Cup', NULL, 'fixture');
\ir ../sql/ddl/002_create_bi_marts.sql
-- Re-applying the script must preserve the views and their contents.
\ir ../sql/ddl/002_create_bi_marts.sql
DO $$
BEGIN
    ASSERT (SELECT COUNT(*) FROM bi_match_facts) = 3;
    ASSERT (SELECT SUM(matches) FROM bi_team_year) = 6;
    ASSERT (SELECT wins + draws + losses = matches FROM bi_team_year WHERE team = 'A' AND year = 2023);
    ASSERT (SELECT win_rate_pct FROM bi_team_year WHERE team = 'A' AND year = 2023) = 50;
    ASSERT (SELECT year_rank FROM bi_team_year WHERE team = 'A' AND year = 2023) = 1;
    ASSERT (SELECT COUNT(*) FROM bi_team_year WHERE year = 2024 AND year_rank = 1) = 2;
    ASSERT (SELECT non_neutral_home_win_pct FROM bi_year_trends WHERE year = 2023) = 100;
    ASSERT (SELECT non_neutral_home_win_pct IS NULL FROM bi_year_trends WHERE year = 2024);
    ASSERT (SELECT cumulative_matches FROM bi_year_trends WHERE year = 2024) = 3;
END $$;
ROLLBACK;
