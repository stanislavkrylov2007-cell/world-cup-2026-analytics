"""Validation helpers for match data files."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date

import pandas as pd

REQUIRED_COLUMNS: tuple[str, ...] = (
    "date",
    "home_team",
    "away_team",
    "home_score",
    "away_score",
    "tournament",
)

OPTIONAL_COLUMNS: tuple[str, ...] = ("city", "country", "neutral")
SUSPICIOUS_SCORE_THRESHOLD = 20
KNOWN_NEUTRAL_VALUES = {True, False, 0, 1, "0", "1", "true", "false", "yes", "no"}


@dataclass(frozen=True)
class ValidationResult:
    """Result of DataFrame validation."""

    is_valid: bool
    errors: list[str]
    warnings: list[str]
    row_count: int
    column_count: int


def validate_required_columns(df: pd.DataFrame) -> list[str]:
    """Check that all required columns are present."""
    missing_columns = [column for column in REQUIRED_COLUMNS if column not in df.columns]
    if not missing_columns:
        return []
    return [f"Missing required columns: {', '.join(missing_columns)}."]


def validate_nulls(df: pd.DataFrame) -> tuple[list[str], list[str]]:
    """Check required fields for nulls and string fields for empty values."""
    errors: list[str] = []
    warnings: list[str] = []

    for column in REQUIRED_COLUMNS:
        if column in df.columns and df[column].isna().any():
            errors.append(f"Required column '{column}' contains missing values.")

    string_columns = [column for column in df.columns if pd.api.types.is_object_dtype(df[column])]
    empty_string_columns: list[str] = []

    for column in string_columns:
        normalized = df[column].dropna().astype(str).str.strip()
        if (normalized == "").any():
            empty_string_columns.append(column)

    if empty_string_columns:
        warnings.append(
            "Empty strings found after trimming spaces in columns: "
            f"{', '.join(sorted(empty_string_columns))}."
        )

    return errors, warnings


def validate_scores(df: pd.DataFrame) -> tuple[list[str], list[str]]:
    """Check that scores are non-negative integers and flag unusual values."""
    errors: list[str] = []
    warnings: list[str] = []

    for column in ("home_score", "away_score"):
        if column not in df.columns:
            continue

        numeric_values = pd.to_numeric(df[column], errors="coerce")
        invalid_mask = numeric_values.isna()
        negative_mask = numeric_values < 0
        non_integer_mask = numeric_values.notna() & (numeric_values % 1 != 0)

        if invalid_mask.any() or negative_mask.any() or non_integer_mask.any():
            errors.append(
                f"Column '{column}' must contain non-negative integer scores."
            )

        suspicious_mask = numeric_values.notna() & (
            numeric_values > SUSPICIOUS_SCORE_THRESHOLD
        )
        if suspicious_mask.any():
            warnings.append(
                f"Column '{column}' contains suspiciously large scores above "
                f"{SUSPICIOUS_SCORE_THRESHOLD}."
            )

    return errors, warnings


def validate_teams(df: pd.DataFrame) -> list[str]:
    """Check that home and away team names are not the same."""
    if "home_team" not in df.columns or "away_team" not in df.columns:
        return []

    home_values = df["home_team"].fillna("").astype(str).str.strip()
    away_values = df["away_team"].fillna("").astype(str).str.strip()
    same_team_mask = (home_values != "") & (home_values == away_values)

    if not same_team_mask.any():
        return []

    return ["home_team must not be equal to away_team."]


def validate_dates(df: pd.DataFrame) -> tuple[list[str], list[str]]:
    """Check that dates are valid datetimes and not in the future."""
    errors: list[str] = []
    warnings: list[str] = []

    if "date" not in df.columns:
        return errors, warnings

    if not pd.api.types.is_datetime64_any_dtype(df["date"]):
        errors.append("Column 'date' must be converted to datetime.")
        return errors, warnings

    if df["date"].isna().any():
        errors.append("Column 'date' contains invalid or missing datetime values.")

    future_mask = df["date"].notna() & (df["date"].dt.date > date.today())
    if future_mask.any():
        warnings.append("Some match dates are in the future.")

    return errors, warnings


def validate_match_dataframe(df: pd.DataFrame) -> ValidationResult:
    """Run all validation checks and return a combined result."""
    errors: list[str] = []
    warnings: list[str] = []
    row_count = len(df.index)
    column_count = len(df.columns)

    if df.empty:
        errors.append("DataFrame is empty.")

    errors.extend(validate_required_columns(df))

    if any(column not in df.columns for column in REQUIRED_COLUMNS):
        return ValidationResult(
            is_valid=False,
            errors=errors,
            warnings=warnings,
            row_count=row_count,
            column_count=column_count,
        )

    null_errors, null_warnings = validate_nulls(df)
    score_errors, score_warnings = validate_scores(df)
    date_errors, date_warnings = validate_dates(df)

    errors.extend(null_errors)
    errors.extend(score_errors)
    errors.extend(validate_teams(df))
    errors.extend(date_errors)

    warnings.extend(null_warnings)
    warnings.extend(score_warnings)
    warnings.extend(date_warnings)

    missing_optional_columns = [
        column for column in OPTIONAL_COLUMNS if column not in df.columns
    ]
    if missing_optional_columns:
        warnings.append(
            "Missing optional columns: "
            f"{', '.join(missing_optional_columns)}."
        )

    if df.duplicated().any():
        warnings.append("Duplicate rows found in the dataset.")

    if "neutral" in df.columns:
        normalized_neutral = (
            df["neutral"]
            .dropna()
            .astype(str)
            .str.strip()
            .str.lower()
        )
        invalid_neutral_mask = ~normalized_neutral.isin(
            {str(value).lower() for value in KNOWN_NEUTRAL_VALUES}
        )
        if invalid_neutral_mask.any():
            warnings.append("Column 'neutral' contains unknown values.")

    return ValidationResult(
        is_valid=not errors,
        errors=errors,
        warnings=warnings,
        row_count=row_count,
        column_count=column_count,
    )
