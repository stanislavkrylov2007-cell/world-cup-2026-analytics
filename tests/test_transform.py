"""Tests for dataset transformation helpers."""

from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

import pandas as pd

from world_cup_analytics.data.transform import (
    load_column_mapping,
    save_transformation_report,
    standardize_neutral_series,
    transform_match_csv,
    transform_matches_dataframe,
    transformation_result_to_markdown,
    validate_column_mapping,
)


def build_source_dataframe() -> pd.DataFrame:
    """Create a source DataFrame for transformation tests."""
    return pd.DataFrame(
        {
            "match_date": ["2024-01-01", "2024-01-02"],
            "home": [" Alpha FC ", "Beta City"],
            "away": ["Gamma Rovers", "Delta Stars"],
            "home_goals": ["1", "2"],
            "away_goals": ["0", "2"],
            "competition": ["Test Cup", "Test Cup"],
            "extra_notes": ["foo", "bar"],
            "neutral_site": [" yes ", "home"],
        }
    )


def build_valid_mapping() -> dict[str, str]:
    """Create a valid internal-to-source column mapping."""
    return {
        "date": "match_date",
        "home_team": "home",
        "away_team": "away",
        "home_score": "home_goals",
        "away_score": "away_goals",
        "tournament": "competition",
        "neutral": "neutral_site",
    }


class TestTransform(unittest.TestCase):
    """Test cases for transformation helpers."""

    def test_load_valid_toml_mapping(self) -> None:
        """A valid TOML mapping file should be loaded."""
        toml_content = """
[source_columns]
date = "match_date"
home_team = "home"
away_team = "away"
home_score = "home_goals"
away_score = "away_goals"
tournament = "competition"
"""
        with tempfile.TemporaryDirectory() as temp_dir:
            mapping_path = Path(temp_dir) / "mapping.toml"
            mapping_path.write_text(toml_content, encoding="utf-8")
            mapping = load_column_mapping(mapping_path)
            self.assertEqual(mapping["date"], "match_date")
            self.assertEqual(mapping["home_team"], "home")

    def test_missing_mapping_file(self) -> None:
        """Missing mapping files should raise FileNotFoundError."""
        with self.assertRaises(FileNotFoundError):
            load_column_mapping(Path("missing.toml"))

    def test_missing_required_mapping(self) -> None:
        """Missing required target fields should be reported."""
        mapping = build_valid_mapping()
        mapping.pop("date")
        errors = validate_column_mapping(build_source_dataframe(), mapping)
        self.assertTrue(any("missing required target fields" in error.lower() for error in errors))

    def test_mapping_to_missing_source_column(self) -> None:
        """Mapping to a missing source column should be reported."""
        mapping = build_valid_mapping()
        mapping["home_team"] = "missing_column"
        errors = validate_column_mapping(build_source_dataframe(), mapping)
        self.assertTrue(any("was not found" in error for error in errors))

    def test_transform_renames_columns(self) -> None:
        """Transformation should rename source columns to contract columns."""
        transformed_df, result = transform_matches_dataframe(
            build_source_dataframe(),
            build_valid_mapping(),
        )
        self.assertTrue(result.is_successful)
        self.assertIn("date", transformed_df.columns)
        self.assertIn("home_team", transformed_df.columns)

    def test_transform_adds_missing_optional_columns(self) -> None:
        """Missing optional fields should be added as NA columns."""
        transformed_df, result = transform_matches_dataframe(
            build_source_dataframe(),
            build_valid_mapping(),
        )
        self.assertIn("city", transformed_df.columns)
        self.assertIn("country", transformed_df.columns)
        self.assertIn("city", result.added_columns)
        self.assertTrue(transformed_df["city"].isna().all())

    def test_transform_drops_extra_source_columns(self) -> None:
        """Extra source columns should not be included in the output."""
        transformed_df, result = transform_matches_dataframe(
            build_source_dataframe(),
            build_valid_mapping(),
        )
        self.assertNotIn("extra_notes", transformed_df.columns)
        self.assertIn("extra_notes", result.dropped_columns)

    def test_transform_trims_strings(self) -> None:
        """String values should be trimmed during transformation."""
        transformed_df, _ = transform_matches_dataframe(
            build_source_dataframe(),
            build_valid_mapping(),
        )
        self.assertEqual(transformed_df.loc[0, "home_team"], "Alpha FC")

    def test_transform_converts_dates(self) -> None:
        """Date values should be converted to datetime."""
        transformed_df, _ = transform_matches_dataframe(
            build_source_dataframe(),
            build_valid_mapping(),
        )
        self.assertTrue(pd.api.types.is_datetime64_any_dtype(transformed_df["date"]))

    def test_transform_converts_integer_scores(self) -> None:
        """Whole-number scores should be converted to nullable integers."""
        transformed_df, _ = transform_matches_dataframe(
            build_source_dataframe(),
            build_valid_mapping(),
        )
        self.assertEqual(str(transformed_df["home_score"].dtype), "Int64")

    def test_transform_refuses_fractional_scores(self) -> None:
        """Fractional scores should make the transformation fail."""
        df = build_source_dataframe()
        df.loc[0, "home_goals"] = "1.5"
        _, result = transform_matches_dataframe(df, build_valid_mapping())
        self.assertFalse(result.is_successful)
        self.assertTrue(any("cannot be safely converted" in error for error in result.errors))

    def test_transform_refuses_negative_scores(self) -> None:
        """Negative scores should fail during final validation."""
        df = build_source_dataframe()
        df.loc[0, "home_goals"] = "-1"
        _, result = transform_matches_dataframe(df, build_valid_mapping())
        self.assertFalse(result.is_successful)
        self.assertTrue(any("non-negative integer scores" in error for error in result.errors))

    def test_standardize_neutral_values(self) -> None:
        """All supported neutral values should be normalized."""
        series = pd.Series(
            ["true", "1", "yes", "y", "neutral", "false", "0", "no", "n", "home", None]
        )
        standardized, warnings = standardize_neutral_series(series)
        self.assertEqual(
            standardized.astype("string").tolist(),
            ["True", "True", "True", "True", "True", "False", "False", "False", "False", "False", pd.NA],
        )
        self.assertEqual(warnings, [])

    def test_standardize_neutral_unknowns(self) -> None:
        """Unknown neutral values should become missing with a warning."""
        series = pd.Series(["maybe", "true"])
        standardized, warnings = standardize_neutral_series(series)
        self.assertTrue(pd.isna(standardized.iloc[0]))
        self.assertEqual(bool(standardized.iloc[1]), True)
        self.assertTrue(any("unknown values" in warning for warning in warnings))

    def test_standardize_neutral_uses_nullable_boolean(self) -> None:
        """Neutral output should use pandas nullable boolean dtype."""
        series = pd.Series(["yes", None])
        standardized, _ = standardize_neutral_series(series)
        self.assertEqual(str(standardized.dtype), "boolean")

    def test_transform_refuses_validation_errors(self) -> None:
        """Final validation errors should prevent success."""
        df = build_source_dataframe()
        df.loc[0, "away"] = " Alpha FC "
        _, result = transform_matches_dataframe(df, build_valid_mapping())
        self.assertFalse(result.is_successful)
        self.assertTrue(any("home_team must not be equal" in error for error in result.errors))

    def test_transform_match_csv_saves_output(self) -> None:
        """Successful transformation should save the standardized CSV."""
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_dir_path = Path(temp_dir)
            source_path = temp_dir_path / "source.csv"
            mapping_path = temp_dir_path / "mapping.toml"
            output_path = temp_dir_path / "output.csv"

            build_source_dataframe().to_csv(source_path, index=False)
            mapping_path.write_text(
                """
[source_columns]
date = "match_date"
home_team = "home"
away_team = "away"
home_score = "home_goals"
away_score = "away_goals"
tournament = "competition"
neutral = "neutral_site"
""",
                encoding="utf-8",
            )

            result = transform_match_csv(source_path, mapping_path, output_path)
            self.assertTrue(result.is_successful)
            self.assertTrue(output_path.exists())

    def test_transform_match_csv_refuses_overwrite(self) -> None:
        """Existing output files should not be overwritten by default."""
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_dir_path = Path(temp_dir)
            source_path = temp_dir_path / "source.csv"
            mapping_path = temp_dir_path / "mapping.toml"
            output_path = temp_dir_path / "output.csv"

            build_source_dataframe().to_csv(source_path, index=False)
            output_path.write_text("existing", encoding="utf-8")
            mapping_path.write_text(
                """
[source_columns]
date = "match_date"
home_team = "home"
away_team = "away"
home_score = "home_goals"
away_score = "away_goals"
tournament = "competition"
neutral = "neutral_site"
""",
                encoding="utf-8",
            )

            result = transform_match_csv(source_path, mapping_path, output_path)
            self.assertFalse(result.is_successful)
            self.assertEqual(output_path.read_text(encoding="utf-8"), "existing")

    def test_transform_match_csv_allows_overwrite(self) -> None:
        """Existing output files may be overwritten explicitly."""
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_dir_path = Path(temp_dir)
            source_path = temp_dir_path / "source.csv"
            mapping_path = temp_dir_path / "mapping.toml"
            output_path = temp_dir_path / "output.csv"

            build_source_dataframe().to_csv(source_path, index=False)
            output_path.write_text("existing", encoding="utf-8")
            mapping_path.write_text(
                """
[source_columns]
date = "match_date"
home_team = "home"
away_team = "away"
home_score = "home_goals"
away_score = "away_goals"
tournament = "competition"
neutral = "neutral_site"
""",
                encoding="utf-8",
            )

            result = transform_match_csv(
                source_path,
                mapping_path,
                output_path,
                overwrite=True,
            )
            self.assertTrue(result.is_successful)
            self.assertIn("date", output_path.read_text(encoding="utf-8"))

    def test_transformation_markdown_report(self) -> None:
        """Transformation result should be rendered as Markdown."""
        _, result = transform_matches_dataframe(build_source_dataframe(), build_valid_mapping())
        report = transformation_result_to_markdown(
            TransformationResultProxy.from_result(result, "source.csv")
        )
        self.assertIn("# Transformation Report", report)
        self.assertIn("## Errors", report)
        self.assertIn("## Warnings", report)

    def test_transformation_report_does_not_include_row_values(self) -> None:
        """The report should not include raw dataset values."""
        df = build_source_dataframe()
        df.loc[0, "home"] = "Top Secret Club"
        _, result = transform_matches_dataframe(df, build_valid_mapping())
        report = transformation_result_to_markdown(
            TransformationResultProxy.from_result(result, "source.csv")
        )
        self.assertNotIn("Top Secret Club", report)

    def test_save_transformation_report(self) -> None:
        """Transformation reports should be written to disk."""
        _, result = transform_matches_dataframe(build_source_dataframe(), build_valid_mapping())
        full_result = TransformationResultProxy.from_result(result, "source.csv")
        with tempfile.TemporaryDirectory() as temp_dir:
            output_path = Path(temp_dir) / "report.md"
            saved_path = save_transformation_report(full_result, output_path)
            self.assertEqual(saved_path, output_path)
            self.assertTrue(output_path.exists())

    def test_source_dataframe_is_unchanged(self) -> None:
        """Transformation should not mutate the input DataFrame."""
        df = build_source_dataframe()
        original_df = df.copy(deep=True)
        transform_matches_dataframe(df, build_valid_mapping())
        pd.testing.assert_frame_equal(df, original_df)

    def test_source_csv_is_unchanged(self) -> None:
        """Transforming a CSV file should not modify the source file."""
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_dir_path = Path(temp_dir)
            source_path = temp_dir_path / "source.csv"
            mapping_path = temp_dir_path / "mapping.toml"
            output_path = temp_dir_path / "output.csv"

            source_df = build_source_dataframe()
            source_df.to_csv(source_path, index=False)
            original_content = source_path.read_text(encoding="utf-8")
            mapping_path.write_text(
                """
[source_columns]
date = "match_date"
home_team = "home"
away_team = "away"
home_score = "home_goals"
away_score = "away_goals"
tournament = "competition"
neutral = "neutral_site"
""",
                encoding="utf-8",
            )

            transform_match_csv(source_path, mapping_path, output_path)
            self.assertEqual(source_path.read_text(encoding="utf-8"), original_content)


class TransformationResultProxy:
    """Helper for building a full result object in tests."""

    @staticmethod
    def from_result(result: object, source_file: str) -> object:
        """Attach the source file field expected by Markdown rendering."""
        from world_cup_analytics.data.transform import TransformationResult

        return TransformationResult(
            source_file=source_file,
            output_file=None,
            input_row_count=result.input_row_count,
            output_row_count=result.output_row_count,
            input_columns=result.input_columns,
            output_columns=result.output_columns,
            renamed_columns=result.renamed_columns,
            added_columns=result.added_columns,
            dropped_columns=result.dropped_columns,
            type_conversions=result.type_conversions,
            warnings=result.warnings,
            errors=result.errors,
            is_successful=result.is_successful,
        )


if __name__ == "__main__":
    unittest.main()
