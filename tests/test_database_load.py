"""Tests for PostgreSQL match loading helpers."""

from __future__ import annotations

import io
import unittest
from contextlib import redirect_stdout
from dataclasses import dataclass
from unittest.mock import MagicMock, patch

import pandas as pd

from world_cup_analytics.database.load_matches import (
    load_matches_dataframe,
    prepare_matches_for_database,
)
from world_cup_analytics.cli import load_postgres_command


def build_standardized_dataframe() -> pd.DataFrame:
    """Create a valid standardized matches DataFrame."""
    return pd.DataFrame(
        {
            "date": pd.to_datetime(["2024-01-01", "2024-01-02"]),
            "home_team": ["Alpha FC", "Beta City"],
            "away_team": ["Gamma Rovers", "Delta Stars"],
            "home_score": [1, 2],
            "away_score": [0, 2],
            "tournament": ["Test Cup", "Test Cup"],
            "city": ["North City", "South City"],
            "country": ["Exampland", "Exampland"],
            "neutral": [False, True],
        }
    )


class FakeResult:
    """Simple scalar result wrapper for fake SQL execution."""

    def __init__(self, value: int) -> None:
        self._value = value

    def scalar_one(self) -> int:
        """Return the wrapped scalar value."""
        return self._value


class FakeTransaction:
    """Context manager that simulates a SQLAlchemy transaction."""

    def __init__(self, connection: "FakeConnection") -> None:
        self.connection = connection

    def __enter__(self) -> "FakeTransaction":
        return self

    def __exit__(self, exc_type, exc, tb) -> bool:
        if exc_type is None:
            self.connection.committed = True
        else:
            self.connection.rolled_back = True
        return False


class FakeConnection:
    """Fake database connection for unit tests."""

    def __init__(self, existing_count: int = 0, fail_on_insert: bool = False) -> None:
        self.existing_count = existing_count
        self.fail_on_insert = fail_on_insert
        self.committed = False
        self.rolled_back = False
        self.executed_statements: list[str] = []
        self.deleted_params: list[dict[str, object]] = []
        self.insert_records: list[dict[str, object]] = []

    def begin(self) -> FakeTransaction:
        """Start a fake transaction."""
        return FakeTransaction(self)

    def execute(self, statement, params=None):
        """Execute a fake SQL statement."""
        statement_text = str(statement)
        self.executed_statements.append(statement_text)

        if "SELECT COUNT(*) FROM matches WHERE source_file" in statement_text:
            return FakeResult(self.existing_count)

        if "DELETE FROM matches WHERE source_file" in statement_text:
            self.deleted_params.append(params)
            self.existing_count = 0
            return FakeResult(0)

        if "INSERT INTO matches" in statement_text:
            if self.fail_on_insert:
                raise RuntimeError("Insert failed")
            assert isinstance(params, list)
            self.insert_records.extend(params)
            self.existing_count += len(params)
            return FakeResult(len(params))

        return FakeResult(0)


@dataclass(frozen=True)
class FakeConfig:
    """Fake app config for CLI tests."""

    db_name: str
    db_password: str
    database_url: str


class TestDatabaseLoad(unittest.TestCase):
    """Test cases for database loading helpers."""

    def test_prepare_dataframe_renames_date_and_adds_source_file(self) -> None:
        """Prepared DataFrame should rename date and add source_file."""
        source_df = build_standardized_dataframe()
        prepared_df = prepare_matches_for_database(source_df, "matches_standardized.csv")
        self.assertIn("match_date", prepared_df.columns)
        self.assertNotIn("date", prepared_df.columns)
        self.assertIn("source_file", prepared_df.columns)
        self.assertEqual(prepared_df["source_file"].iloc[0], "matches_standardized.csv")

    def test_prepare_dataframe_does_not_mutate_source(self) -> None:
        """Preparing data should not modify the input DataFrame."""
        source_df = build_standardized_dataframe()
        original_df = source_df.copy(deep=True)
        prepare_matches_for_database(source_df, "matches_standardized.csv")
        pd.testing.assert_frame_equal(source_df, original_df)

    def test_prepare_dataframe_rejects_validation_errors(self) -> None:
        """Invalid DataFrames should be rejected before loading."""
        source_df = build_standardized_dataframe()
        source_df.loc[0, "away_team"] = "Alpha FC"
        with self.assertRaises(ValueError):
            prepare_matches_for_database(source_df, "matches_standardized.csv")

    def test_load_dataframe_commits_transaction(self) -> None:
        """Successful loads should commit the transaction."""
        connection = FakeConnection(existing_count=0)
        loaded_count = load_matches_dataframe(
            connection=connection,
            df=build_standardized_dataframe(),
            source_file="matches_standardized.csv",
        )
        self.assertEqual(loaded_count, 2)
        self.assertTrue(connection.committed)
        self.assertFalse(connection.rolled_back)

    def test_load_dataframe_rolls_back_on_error(self) -> None:
        """Failing inserts should trigger rollback."""
        connection = FakeConnection(existing_count=0, fail_on_insert=True)
        with self.assertRaises(RuntimeError):
            load_matches_dataframe(
                connection=connection,
                df=build_standardized_dataframe(),
                source_file="matches_standardized.csv",
            )
        self.assertTrue(connection.rolled_back)
        self.assertFalse(connection.committed)

    def test_repeat_load_without_replace_is_rejected(self) -> None:
        """Existing source_file rows should block duplicate loads."""
        connection = FakeConnection(existing_count=5)
        with self.assertRaises(ValueError):
            load_matches_dataframe(
                connection=connection,
                df=build_standardized_dataframe(),
                source_file="matches_standardized.csv",
                replace=False,
            )
        self.assertEqual(connection.insert_records, [])

    def test_replace_deletes_only_same_source_file_rows(self) -> None:
        """replace=True should delete only rows for the same source_file."""
        connection = FakeConnection(existing_count=5)
        loaded_count = load_matches_dataframe(
            connection=connection,
            df=build_standardized_dataframe(),
            source_file="matches_standardized.csv",
            replace=True,
        )
        self.assertEqual(loaded_count, 2)
        self.assertEqual(
            connection.deleted_params,
            [{"source_file": "matches_standardized.csv"}],
        )

    def test_load_returns_inserted_row_count(self) -> None:
        """The loader should return the number of inserted rows."""
        connection = FakeConnection(existing_count=0)
        loaded_count = load_matches_dataframe(
            connection=connection,
            df=build_standardized_dataframe(),
            source_file="matches_standardized.csv",
        )
        self.assertEqual(loaded_count, 2)

    def test_cli_output_does_not_include_password(self) -> None:
        """CLI output should not reveal secrets."""
        fake_config = FakeConfig(
            db_name="world_cup_analytics",
            db_password="super_secret_password",
            database_url="postgresql+psycopg://user:pass@localhost/db",
        )
        fake_engine = MagicMock()
        fake_context_connection = FakeConnection(existing_count=0)
        fake_engine.connect.return_value.__enter__.return_value = fake_context_connection
        fake_engine.connect.return_value.__exit__.return_value = False

        buffer = io.StringIO()
        with patch("world_cup_analytics.cli.load_config", return_value=fake_config), patch(
            "world_cup_analytics.cli.load_and_validate_match_csv",
            return_value=(build_standardized_dataframe(), MagicMock(errors=[])),
        ), patch("world_cup_analytics.cli._create_engine", return_value=fake_engine), patch(
            "sys.argv",
            ["wca-load-postgres", "data/interim/matches_standardized.csv"],
        ), redirect_stdout(buffer), self.assertRaises(SystemExit) as exit_context:
            load_postgres_command()

        output = buffer.getvalue()
        self.assertEqual(exit_context.exception.code, 0)
        self.assertNotIn("super_secret_password", output)


if __name__ == "__main__":
    unittest.main()
