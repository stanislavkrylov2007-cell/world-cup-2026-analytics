CREATE TABLE IF NOT EXISTS matches (
    match_id BIGSERIAL PRIMARY KEY,
    match_date DATE NOT NULL,
    home_team TEXT NOT NULL,
    away_team TEXT NOT NULL,
    home_score INTEGER NOT NULL CHECK (home_score >= 0),
    away_score INTEGER NOT NULL CHECK (away_score >= 0),
    tournament TEXT NOT NULL,
    city TEXT NULL,
    country TEXT NULL,
    neutral BOOLEAN NULL,
    source_file TEXT NOT NULL,
    loaded_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    CONSTRAINT matches_different_teams CHECK (home_team <> away_team)
);

CREATE INDEX IF NOT EXISTS idx_matches_match_date ON matches (match_date);
CREATE INDEX IF NOT EXISTS idx_matches_home_team ON matches (home_team);
CREATE INDEX IF NOT EXISTS idx_matches_away_team ON matches (away_team);
CREATE INDEX IF NOT EXISTS idx_matches_tournament ON matches (tournament);
CREATE INDEX IF NOT EXISTS idx_matches_country ON matches (country);
