"""Data loading and preparation helpers for the Streamlit dashboard."""

from __future__ import annotations

import os
from pathlib import Path
from typing import Any

import pandas as pd
import streamlit as st

PROJECT_ROOT = Path(__file__).resolve().parents[1]
ENV_PATH = PROJECT_ROOT / ".env"
CSV_PATH = PROJECT_ROOT / "data" / "interim" / "matches_standardized.csv"

MATCH_COLUMNS: tuple[str, ...] = (
    "date",
    "home_team",
    "away_team",
    "home_score",
    "away_score",
    "tournament",
    "city",
    "country",
    "neutral",
)


def _load_env_file(env_path: Path) -> dict[str, str]:
    """Read simple key-value pairs from a local .env file."""
    values: dict[str, str] = {}
    if not env_path.exists():
        return values

    for raw_line in env_path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        values[key.strip()] = value.strip()
    return values


def _build_database_url() -> str | None:
    """Build a PostgreSQL URL from environment variables when available."""
    env = dict(os.environ)
    env.update(_load_env_file(ENV_PATH))

    required_keys = ("DB_HOST", "DB_PORT", "DB_NAME", "DB_USER", "DB_PASSWORD")
    if not all(env.get(key) for key in required_keys):
        return None

    return (
        f"postgresql+psycopg://{env['DB_USER']}:{env['DB_PASSWORD']}"
        f"@{env['DB_HOST']}:{env['DB_PORT']}/{env['DB_NAME']}"
    )


def _read_matches_from_postgres() -> pd.DataFrame:
    """Load matches from PostgreSQL."""
    from sqlalchemy import create_engine, text

    database_url = _build_database_url()
    if database_url is None:
        raise RuntimeError("PostgreSQL environment variables are not configured.")

    query = text(
        """
        SELECT
            match_date AS date,
            home_team,
            away_team,
            home_score,
            away_score,
            tournament,
            city,
            country,
            neutral
        FROM matches
        ORDER BY match_date
        """
    )

    engine = create_engine(database_url)
    with engine.connect() as connection:
        return pd.read_sql(query, connection)


def _read_matches_from_csv() -> pd.DataFrame:
    """Load matches from the standardized CSV fallback."""
    if not CSV_PATH.exists():
        raise FileNotFoundError(
            "CSV fallback file is missing: data/interim/matches_standardized.csv"
        )
    return pd.read_csv(CSV_PATH)


def _prepare_matches(df: pd.DataFrame) -> pd.DataFrame:
    """Prepare raw match data for filtering and visualization."""
    prepared_df = df.copy(deep=True)

    for column in MATCH_COLUMNS:
        if column not in prepared_df.columns:
            prepared_df[column] = pd.NA

    prepared_df = prepared_df.loc[:, list(MATCH_COLUMNS)]
    prepared_df["date"] = pd.to_datetime(prepared_df["date"], errors="coerce")
    prepared_df["home_score"] = pd.to_numeric(
        prepared_df["home_score"], errors="coerce"
    )
    prepared_df["away_score"] = pd.to_numeric(
        prepared_df["away_score"], errors="coerce"
    )
    prepared_df["neutral"] = prepared_df["neutral"].astype("boolean")

    prepared_df["year"] = prepared_df["date"].dt.year
    prepared_df["total_goals"] = prepared_df["home_score"] + prepared_df["away_score"]
    prepared_df["goal_difference"] = (
        prepared_df["home_score"] - prepared_df["away_score"]
    ).abs()

    prepared_df["result"] = "Draw"
    prepared_df.loc[
        prepared_df["home_score"] > prepared_df["away_score"], "result"
    ] = "Home win"
    prepared_df.loc[
        prepared_df["home_score"] < prepared_df["away_score"], "result"
    ] = "Away win"

    return prepared_df.sort_values("date").reset_index(drop=True)


@st.cache_data(show_spinner=False)
def load_matches() -> tuple[pd.DataFrame | None, str | None, str | None, str | None]:
    """Load matches from PostgreSQL with CSV fallback."""
    postgres_error: str | None = None

    try:
        df = _read_matches_from_postgres()
        return _prepare_matches(df), "PostgreSQL table: matches", None, None
    except Exception as error:  # pragma: no cover - UI fallback branch
        postgres_error = error.__class__.__name__

    try:
        df = _read_matches_from_csv()
        info_message = "Running with the standardized CSV fallback dataset."
        details_message = (
            "PostgreSQL is unavailable in the current environment, so the dashboard "
            "is using the local CSV file instead."
        )
        if postgres_error:
            details_message = f"{details_message} Database error type: {postgres_error}."
        return (
            _prepare_matches(df),
            "CSV fallback: data/interim/matches_standardized.csv",
            info_message,
            details_message,
        )
    except Exception:
        instructions = (
            "Data is unavailable. First load the `matches` table into PostgreSQL or "
            "prepare `data/interim/matches_standardized.csv` using the project ETL "
            "commands."
        )
        return None, None, None, instructions


def get_filter_options(matches_df: pd.DataFrame) -> dict[str, Any]:
    """Build sidebar filter options from the available dataset."""
    teams = pd.Index(
        sorted(
            pd.unique(
                pd.concat([matches_df["home_team"], matches_df["away_team"]]).dropna()
            ).tolist()
        )
    )
    tournaments = pd.Index(sorted(matches_df["tournament"].dropna().unique().tolist()))
    countries = pd.Index(sorted(matches_df["country"].dropna().unique().tolist()))

    year_min = int(matches_df["year"].dropna().min())
    year_max = int(matches_df["year"].dropna().max())

    return {
        "teams": teams.tolist(),
        "tournaments": tournaments.tolist(),
        "countries": countries.tolist(),
        "year_min": year_min,
        "year_max": year_max,
    }


def apply_global_filters(
    matches_df: pd.DataFrame,
    year_range: tuple[int, int],
    tournament: str,
    team: str,
    country: str,
    venue_mode: str,
) -> pd.DataFrame:
    """Apply global dashboard filters to the match dataset."""
    filtered_df = matches_df.copy(deep=False)

    filtered_df = filtered_df.loc[
        filtered_df["year"].between(year_range[0], year_range[1], inclusive="both")
    ]

    if tournament != "All":
        filtered_df = filtered_df.loc[filtered_df["tournament"] == tournament]

    if team != "All":
        filtered_df = filtered_df.loc[
            (filtered_df["home_team"] == team) | (filtered_df["away_team"] == team)
        ]

    if country != "All":
        filtered_df = filtered_df.loc[filtered_df["country"] == country]

    if venue_mode == "Only neutral":
        filtered_df = filtered_df.loc[filtered_df["neutral"] == True]  # noqa: E712
    elif venue_mode == "Only non-neutral":
        filtered_df = filtered_df.loc[filtered_df["neutral"] == False]  # noqa: E712

    return filtered_df.sort_values("date").reset_index(drop=True)


@st.cache_data(show_spinner=False)
def build_team_long(matches_df: pd.DataFrame) -> pd.DataFrame:
    """Create a team-centric long table from home and away perspectives."""
    home_df = matches_df[
        [
            "date",
            "year",
            "home_team",
            "away_team",
            "home_score",
            "away_score",
            "tournament",
            "city",
            "country",
            "neutral",
            "total_goals",
            "goal_difference",
        ]
    ].copy()
    home_df["team"] = home_df["home_team"]
    home_df["opponent"] = home_df["away_team"]
    home_df["goals_for"] = home_df["home_score"]
    home_df["goals_against"] = home_df["away_score"]
    home_df["venue_role"] = "Home"

    away_df = matches_df[
        [
            "date",
            "year",
            "home_team",
            "away_team",
            "home_score",
            "away_score",
            "tournament",
            "city",
            "country",
            "neutral",
            "total_goals",
            "goal_difference",
        ]
    ].copy()
    away_df["team"] = away_df["away_team"]
    away_df["opponent"] = away_df["home_team"]
    away_df["goals_for"] = away_df["away_score"]
    away_df["goals_against"] = away_df["home_score"]
    away_df["venue_role"] = "Away"

    team_df = pd.concat([home_df, away_df], ignore_index=True)
    team_df["match_result"] = "Draw"
    team_df.loc[team_df["goals_for"] > team_df["goals_against"], "match_result"] = "Win"
    team_df.loc[team_df["goals_for"] < team_df["goals_against"], "match_result"] = "Loss"
    team_df["is_win"] = (team_df["match_result"] == "Win").astype(int)
    team_df["is_draw"] = (team_df["match_result"] == "Draw").astype(int)
    team_df["is_loss"] = (team_df["match_result"] == "Loss").astype(int)
    return team_df


def summarize_team(team_matches_df: pd.DataFrame) -> dict[str, float | int]:
    """Compute KPI values for a selected team."""
    match_count = int(len(team_matches_df.index))
    wins = int(team_matches_df["is_win"].sum())
    draws = int(team_matches_df["is_draw"].sum())
    losses = int(team_matches_df["is_loss"].sum())
    goals_for = int(team_matches_df["goals_for"].sum())
    goals_against = int(team_matches_df["goals_against"].sum())

    return {
        "matches": match_count,
        "wins": wins,
        "draws": draws,
        "losses": losses,
        "win_rate": (wins / match_count * 100) if match_count else 0.0,
        "goals_for": goals_for,
        "goals_against": goals_against,
        "goal_difference": goals_for - goals_against,
        "avg_goals_for": (goals_for / match_count) if match_count else 0.0,
    }


def yearly_team_results(team_matches_df: pd.DataFrame) -> pd.DataFrame:
    """Aggregate team results by year."""
    return (
        team_matches_df.groupby("year", as_index=False)
        .agg(
            matches=("team", "size"),
            wins=("is_win", "sum"),
            draws=("is_draw", "sum"),
            losses=("is_loss", "sum"),
            goals_for=("goals_for", "sum"),
            goals_against=("goals_against", "sum"),
        )
        .sort_values("year")
    )


def top_team_opponents(team_matches_df: pd.DataFrame, limit: int = 10) -> pd.DataFrame:
    """Return the most common opponents for a selected team."""
    return (
        team_matches_df.groupby("opponent", as_index=False)
        .agg(matches=("team", "size"), wins=("is_win", "sum"))
        .sort_values(["matches", "wins", "opponent"], ascending=[False, False, True])
        .head(limit)
    )


def latest_team_matches(team_matches_df: pd.DataFrame, limit: int = 20) -> pd.DataFrame:
    """Return the latest matches for the selected team."""
    output_df = team_matches_df.sort_values("date", ascending=False).head(limit).copy()
    return output_df[
        [
            "date",
            "team",
            "opponent",
            "goals_for",
            "goals_against",
            "match_result",
            "tournament",
            "city",
            "country",
            "neutral",
            "venue_role",
        ]
    ]


def tournament_team_summary(matches_df: pd.DataFrame) -> pd.DataFrame:
    """Build a team ranking inside a filtered tournament slice."""
    team_df = build_team_long(matches_df)
    return (
        team_df.groupby("team", as_index=False)
        .agg(matches=("team", "size"), wins=("is_win", "sum"))
        .sort_values(["wins", "matches", "team"], ascending=[False, False, True])
    )


def biggest_wins(matches_df: pd.DataFrame, limit: int = 10) -> pd.DataFrame:
    """Return the biggest wins in the filtered dataset."""
    output_df = matches_df.copy()
    output_df["winner"] = output_df["home_team"]
    output_df["loser"] = output_df["away_team"]
    output_df.loc[output_df["away_score"] > output_df["home_score"], "winner"] = (
        output_df["away_team"]
    )
    output_df.loc[output_df["away_score"] > output_df["home_score"], "loser"] = (
        output_df["home_team"]
    )

    return (
        output_df.sort_values(
            ["goal_difference", "total_goals", "date"], ascending=[False, False, False]
        )
        .head(limit)
        .loc[
            :,
            [
                "date",
                "home_team",
                "away_team",
                "home_score",
                "away_score",
                "goal_difference",
                "tournament",
                "country",
            ],
        ]
    )


def apply_match_explorer_filters(
    matches_df: pd.DataFrame,
    team_search: str,
    min_total_goals: int,
    draws_only: bool,
    big_wins_only: bool,
    limit: int = 500,
) -> pd.DataFrame:
    """Apply local filters for the match explorer tab."""
    filtered_df = matches_df.copy(deep=False)

    if team_search.strip():
        needle = team_search.strip().casefold()
        filtered_df = filtered_df.loc[
            filtered_df["home_team"].str.casefold().str.contains(needle, na=False)
            | filtered_df["away_team"].str.casefold().str.contains(needle, na=False)
        ]

    filtered_df = filtered_df.loc[filtered_df["total_goals"] >= min_total_goals]

    if draws_only:
        filtered_df = filtered_df.loc[filtered_df["result"] == "Draw"]

    if big_wins_only:
        filtered_df = filtered_df.loc[filtered_df["goal_difference"] >= 5]

    filtered_df = filtered_df.sort_values("date", ascending=False)
    return filtered_df.head(limit).reset_index(drop=True)
