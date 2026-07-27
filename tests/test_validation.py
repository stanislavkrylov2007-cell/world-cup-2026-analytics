"""Tests for DataFrame validation."""

from __future__ import annotations

import unittest

import pandas as pd

from world_cup_analytics.data.validation import validate_match_dataframe


def build_valid_dataframe() -> pd.DataFrame:
    """Create a valid DataFrame for validation tests."""
    return pd.DataFrame(
        {
            "date": pd.to_datetime(["2024-01-01", "2024-01-02"]),
            "home_team": ["Alpha United", "Beta City"],
            "away_team": ["Gamma Rovers", "Delta Stars"],
            "home_score": [1, 2],
            "away_score": [0, 2],
            "tournament": ["Test Cup", "Test Cup"],
            "city": ["North City", "South City"],
            "country": ["Exampland", "Exampland"],
            "neutral": [False, True],
        }
    )


class TestValidation(unittest.TestCase):
    """Test cases for the validation module."""

    def test_valid_dataframe(self) -> None:
        """A correct DataFrame should pass validation."""
        result = validate_match_dataframe(build_valid_dataframe())
        self.assertTrue(result.is_valid)
        self.assertEqual(result.errors, [])

    def test_missing_required_column(self) -> None:
        """Missing required columns should be reported as errors."""
        df = build_valid_dataframe().drop(columns=["tournament"])
        result = validate_match_dataframe(df)
        self.assertFalse(result.is_valid)
        self.assertTrue(any("Missing required columns" in error for error in result.errors))

    def test_empty_dataframe(self) -> None:
        """An empty DataFrame should produce an error."""
        df = pd.DataFrame(columns=build_valid_dataframe().columns)
        result = validate_match_dataframe(df)
        self.assertFalse(result.is_valid)
        self.assertIn("DataFrame is empty.", result.errors)

    def test_negative_score(self) -> None:
        """Negative scores should be rejected."""
        df = build_valid_dataframe()
        df.loc[0, "home_score"] = -1
        result = validate_match_dataframe(df)
        self.assertFalse(result.is_valid)
        self.assertTrue(any("home_score" in error for error in result.errors))

    def test_fractional_score(self) -> None:
        """Fractional scores should be rejected."""
        df = build_valid_dataframe()
        df["away_score"] = df["away_score"].astype(float)
        df.loc[0, "away_score"] = 1.5
        result = validate_match_dataframe(df)
        self.assertFalse(result.is_valid)
        self.assertTrue(any("away_score" in error for error in result.errors))

    def test_same_home_and_away_team(self) -> None:
        """The same team on both sides should be rejected."""
        df = build_valid_dataframe()
        df.loc[0, "away_team"] = "Alpha United"
        result = validate_match_dataframe(df)
        self.assertFalse(result.is_valid)
        self.assertIn("home_team must not be equal to away_team.", result.errors)

    def test_invalid_date(self) -> None:
        """Invalid datetime values should produce an error."""
        df = build_valid_dataframe()
        df.loc[0, "date"] = pd.NaT
        result = validate_match_dataframe(df)
        self.assertFalse(result.is_valid)
        self.assertTrue(any("date" in error for error in result.errors))

    def test_future_date_warning(self) -> None:
        """Future dates should produce a warning."""
        df = build_valid_dataframe()
        df.loc[0, "date"] = pd.Timestamp("2099-01-01")
        result = validate_match_dataframe(df)
        self.assertTrue(any("future" in warning.lower() for warning in result.warnings))

    def test_duplicate_warning(self) -> None:
        """Duplicate rows should produce a warning."""
        df = pd.concat([build_valid_dataframe(), build_valid_dataframe().iloc[[0]]], ignore_index=True)
        result = validate_match_dataframe(df)
        self.assertTrue(any("Duplicate rows" in warning for warning in result.warnings))

    def test_missing_optional_columns_warning(self) -> None:
        """Missing optional columns should be reported as warnings."""
        df = build_valid_dataframe().drop(columns=["city", "country", "neutral"])
        result = validate_match_dataframe(df)
        self.assertTrue(any("Missing optional columns" in warning for warning in result.warnings))


if __name__ == "__main__":
    unittest.main()
