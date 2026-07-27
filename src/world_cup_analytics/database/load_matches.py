"""Load standardized football matches into PostgreSQL."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import pandas as pd

from world_cup_analytics.config import load_config
from world_cup_analytics.data.loader import load_match_csv
from world_cup_analytics.data.validation import validate_match_dataframe

MATCHES_TABLE_COLUMNS: tuple[str, ...] = (
    "match_date",
    "home_team",
    "away_team",
    "home_score",
    "away_score",
    "tournament",
    "city",
    "country",
    "neutral",
    "source_file",
)


def _sql_text(statement: str) -> Any:
    """Return a SQLAlchemy text object when available, or a raw string in tests."""
    try:
        from sqlalchemy import text
    except ModuleNotFoundError:
        return statement
    return text(statement)


def _create_engine(database_url: Any) -> Any:
    """Create a SQLAlchemy engine when SQLAlchemy is available."""
    try:
        from sqlalchemy import create_engine
    except ModuleNotFoundError as error:
        raise RuntimeError(
            "SQLAlchemy is required for real PostgreSQL loading but is not installed."
        ) from error
    return create_engine(database_url)


def prepare_matches_for_database(df: pd.DataFrame, source_file: str) -> pd.DataFrame:
    """Prepare a standardized DataFrame for insertion into PostgreSQL."""
    validation_result = validate_match_dataframe(df)
    if validation_result.errors:
        joined_errors = "; ".join(validation_result.errors)
        raise ValueError(
            "Standardized DataFrame is not valid for database loading: "
            f"{joined_errors}"
        )

    prepared_df = df.copy(deep=True)
    prepared_df = prepared_df.rename(columns={"date": "match_date"})
    prepared_df["source_file"] = source_file

    prepared_df["match_date"] = prepared_df["match_date"].dt.date
    prepared_df["home_score"] = prepared_df["home_score"].astype("Int64")
    prepared_df["away_score"] = prepared_df["away_score"].astype("Int64")
    prepared_df["neutral"] = prepared_df["neutral"].astype("boolean")

    for column in ("city", "country"):
        if column in prepared_df.columns:
            prepared_df[column] = prepared_df[column].astype("string")

    prepared_df = prepared_df.loc[:, list(MATCHES_TABLE_COLUMNS)]
    prepared_df = prepared_df.where(pd.notna(prepared_df), None)
    return prepared_df


def create_matches_table(connection: Any) -> None:
    """Create the matches table if it does not exist."""
    ddl_path = Path("sql") / "ddl" / "001_create_matches.sql"
    ddl_sql = ddl_path.read_text(encoding="utf-8")
    _execute_sql_script(connection, ddl_sql)


def load_matches_dataframe(
    connection: Any,
    df: pd.DataFrame,
    source_file: str,
    replace: bool = False,
) -> int:
    """Load a validated standardized DataFrame into PostgreSQL."""
    prepared_df = prepare_matches_for_database(df, source_file=source_file)

    insert_sql = _sql_text(
        """
        INSERT INTO matches (
            match_date,
            home_team,
            away_team,
            home_score,
            away_score,
            tournament,
            city,
            country,
            neutral,
            source_file
        )
        VALUES (
            :match_date,
            :home_team,
            :away_team,
            :home_score,
            :away_score,
            :tournament,
            :city,
            :country,
            :neutral,
            :source_file
        )
        """
    )
    count_sql = _sql_text(
        "SELECT COUNT(*) FROM matches WHERE source_file = :source_file"
    )
    delete_sql = _sql_text(
        "DELETE FROM matches WHERE source_file = :source_file"
    )

    try:
        with connection.begin():
            create_matches_table(connection)
            existing_count = int(
                connection.execute(
                    count_sql, {"source_file": source_file}
                ).scalar_one()
            )

            if existing_count > 0 and not replace:
                raise ValueError(
                    f"Rows for source_file '{source_file}' already exist in matches."
                )

            if existing_count > 0 and replace:
                connection.execute(delete_sql, {"source_file": source_file})

            records = prepared_df.to_dict(orient="records")
            if records:
                connection.execute(insert_sql, records)
        return len(prepared_df.index)
    except Exception:
        raise


def load_matches_csv(
    csv_path: Path,
    replace: bool = False,
) -> int:
    """Load a standardized CSV file into PostgreSQL."""
    if csv_path.suffix.lower() != ".csv":
        raise ValueError(f"Expected a .csv file, got: {csv_path.name}")

    df = load_match_csv(csv_path)
    source_file = csv_path.name

    config = load_config()
    engine = _create_engine(config.database_url)
    with engine.connect() as connection:
        loaded_row_count = load_matches_dataframe(
            connection=connection,
            df=df,
            source_file=source_file,
            replace=replace,
        )
    return loaded_row_count


def _execute_sql_script(connection: Any, sql_script: str) -> None:
    """Execute a SQL script statement by statement."""
    statements = [statement.strip() for statement in sql_script.split(";")]
    for statement in statements:
        if statement:
            connection.execute(_sql_text(statement))
