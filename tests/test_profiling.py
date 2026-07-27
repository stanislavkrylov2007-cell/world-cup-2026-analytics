"""Tests for dataset profiling helpers."""

from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

import pandas as pd

from world_cup_analytics.data.profiling import (
    build_dataset_profile,
    profile_to_markdown,
    save_profile_report,
)
from world_cup_analytics.data.validation import ValidationResult


def build_profile_dataframe() -> pd.DataFrame:
    """Create a DataFrame for profiling tests."""
    return pd.DataFrame(
        {
            "date": pd.to_datetime(["2024-01-01", "2024-01-03", None]),
            "home_team": ["Alpha", "Beta", "Alpha"],
            "away_team": ["Gamma", "Delta", "Gamma"],
            "home_score": [1, 2, 1],
            "away_score": [0, 2, 0],
            "tournament": ["Cup A", "Cup B", "Cup A"],
            "neutral": [False, True, False],
        }
    )


class TestProfiling(unittest.TestCase):
    """Test cases for dataset profiling."""

    def test_build_profile_counts_rows_and_columns(self) -> None:
        """Profile should include row and column counts."""
        profile = build_dataset_profile(build_profile_dataframe(), "matches.csv")
        self.assertEqual(profile.row_count, 3)
        self.assertEqual(profile.column_count, 7)

    def test_build_profile_counts_missing_values(self) -> None:
        """Profile should count missing values and percentages."""
        profile = build_dataset_profile(build_profile_dataframe(), "matches.csv")
        self.assertEqual(profile.missing_values["date"], 1)
        self.assertEqual(profile.missing_percentages["date"], 33.33)

    def test_build_profile_counts_duplicates(self) -> None:
        """Profile should count full duplicate rows."""
        df = build_profile_dataframe()
        df = pd.concat([df, df.iloc[[0]]], ignore_index=True)
        profile = build_dataset_profile(df, "matches.csv")
        self.assertEqual(profile.duplicate_row_count, 1)

    def test_build_profile_infers_dtypes(self) -> None:
        """Profile should store inferred dtypes."""
        profile = build_dataset_profile(build_profile_dataframe(), "matches.csv")
        self.assertTrue(profile.inferred_dtypes["date"].startswith("datetime64["))

    def test_build_profile_tracks_date_range(self) -> None:
        """Profile should include min and max valid dates."""
        profile = build_dataset_profile(build_profile_dataframe(), "matches.csv")
        self.assertEqual(profile.date_min, "2024-01-01")
        self.assertEqual(profile.date_max, "2024-01-03")

    def test_build_profile_counts_entities(self) -> None:
        """Profile should count teams and tournaments."""
        profile = build_dataset_profile(build_profile_dataframe(), "matches.csv")
        self.assertEqual(profile.home_team_count, 2)
        self.assertEqual(profile.away_team_count, 2)
        self.assertEqual(profile.tournament_count, 2)

    def test_profile_without_optional_columns(self) -> None:
        """Missing optional columns should not break profiling."""
        df = build_profile_dataframe().drop(columns=["neutral"])
        profile = build_dataset_profile(df, "matches.csv")
        self.assertEqual(profile.column_count, 6)
        self.assertNotIn("neutral", profile.columns)

    def test_profile_without_date_column(self) -> None:
        """Missing date column should result in empty date coverage."""
        df = build_profile_dataframe().drop(columns=["date"])
        profile = build_dataset_profile(df, "matches.csv")
        self.assertIsNone(profile.date_min)
        self.assertIsNone(profile.date_max)

    def test_profile_with_non_datetime_dates(self) -> None:
        """Non-datetime date columns should not break profiling."""
        df = build_profile_dataframe()
        df["date"] = ["bad-date", "2024-01-03", None]
        profile = build_dataset_profile(df, "matches.csv")
        self.assertIsNone(profile.date_min)
        self.assertIsNone(profile.date_max)
        self.assertIn(profile.inferred_dtypes["date"], {"object", "str", "string"})

    def test_empty_dataframe_profile(self) -> None:
        """Empty DataFrames should still produce a profile."""
        df = pd.DataFrame(columns=["date", "home_team"])
        profile = build_dataset_profile(df, "matches.csv")
        self.assertEqual(profile.row_count, 0)
        self.assertEqual(profile.missing_percentages["date"], 0.0)

    def test_profile_includes_validation_messages(self) -> None:
        """Validation messages should be preserved in the profile."""
        validation_result = ValidationResult(
            is_valid=False,
            errors=["Example error"],
            warnings=["Example warning"],
            row_count=3,
            column_count=7,
        )
        profile = build_dataset_profile(
            build_profile_dataframe(),
            "matches.csv",
            validation_result=validation_result,
        )
        self.assertEqual(profile.validation_errors, ["Example error"])
        self.assertEqual(profile.validation_warnings, ["Example warning"])

    def test_profile_to_markdown_creates_expected_sections(self) -> None:
        """Markdown report should contain the required sections."""
        profile = build_dataset_profile(build_profile_dataframe(), "matches.csv")
        markdown = profile_to_markdown(profile)
        self.assertIn("## Dataset overview", markdown)
        self.assertIn("## Columns and inferred types", markdown)
        self.assertIn("## Missing values", markdown)
        self.assertIn("## Cardinality", markdown)
        self.assertIn("## Date coverage", markdown)
        self.assertIn("## Match entities", markdown)
        self.assertIn("## Validation errors", markdown)
        self.assertIn("## Validation warnings", markdown)
        self.assertIn("## Limitations", markdown)

    def test_profile_report_does_not_include_row_values(self) -> None:
        """Markdown should not include raw row values from the dataset."""
        df = build_profile_dataframe()
        df.loc[0, "home_team"] = "Very Secret Team Name"
        profile = build_dataset_profile(df, "matches.csv")
        markdown = profile_to_markdown(profile)
        self.assertNotIn("Very Secret Team Name", markdown)

    def test_save_profile_report(self) -> None:
        """Profile report should be saved to the requested path."""
        profile = build_dataset_profile(build_profile_dataframe(), "matches.csv")
        with tempfile.TemporaryDirectory() as temp_dir:
            output_path = Path(temp_dir) / "profile.md"
            saved_path = save_profile_report(profile, output_path)
            self.assertEqual(saved_path, output_path)
            self.assertTrue(output_path.exists())
            self.assertIn("Data Profile Report", output_path.read_text(encoding="utf-8"))


if __name__ == "__main__":
    unittest.main()
