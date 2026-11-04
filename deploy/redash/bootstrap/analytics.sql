\set ON_ERROR_STOP on
\i /bootstrap/001_create_matches.sql
CREATE TEMP TABLE incoming_matches (
 match_date date, home_team text, away_team text, home_score integer,
 away_score integer, tournament text, city text, country text, neutral boolean
);
COPY incoming_matches FROM '/bootstrap/matches.csv' WITH (FORMAT csv, HEADER true);
INSERT INTO matches (match_date,home_team,away_team,home_score,away_score,tournament,city,country,neutral,source_file)
SELECT *, 'matches_standardized.csv' FROM incoming_matches;
\i /bootstrap/002_create_bi_marts.sql
CREATE ROLE redash_reader LOGIN PASSWORD :'reader_password';
GRANT CONNECT ON DATABASE world_cup_analytics TO redash_reader;
GRANT USAGE ON SCHEMA public TO redash_reader;
GRANT SELECT ON ALL TABLES IN SCHEMA public TO redash_reader;
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT SELECT ON TABLES TO redash_reader;
DO $$ BEGIN
 IF (SELECT COUNT(*) FROM matches) <> 49520 THEN RAISE EXCEPTION 'Unexpected match count'; END IF;
END $$;
