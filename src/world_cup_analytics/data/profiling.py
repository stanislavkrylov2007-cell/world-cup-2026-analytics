"""Dataset profiling helpers for match CSV files."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from datetime import datetime
from pathlib import Path
import re

import pandas as pd

from world_cup_analytics.data.loader import load_and_validate_match_csv
from world_cup_analytics.data.validation import ValidationResult


@dataclass(frozen=True)
class DatasetProfile:
    """Aggregated profile of a loaded dataset."""

    source_file: str
    generated_at: datetime
    row_count: int
    column_count: int
    columns: list[str]
    duplicate_row_count: int
    missing_values: dict[str, int]
    missing_percentages: dict[str, float]
    inferred_dtypes: dict[str, str]
    unique_values: dict[str, int]
    date_min: str | None
    date_max: str | None
    home_team_count: int | None
    away_team_count: int | None
    tournament_count: int | None
    validation_errors: list[str]
    validation_warnings: list[str]


def build_dataset_profile(
    df: pd.DataFrame,
    source_file: str,
    validation_result: ValidationResult | None = None,
) -> DatasetProfile:
    """Build an aggregated dataset profile from a loaded DataFrame."""
    row_count = len(df.index)
    column_count = len(df.columns)
    columns = list(df.columns)
    duplicate_row_count = int(df.duplicated().sum())
    missing_values = {
        column: int(df[column].isna().sum()) for column in df.columns
    }
    missing_percentages = {
        column: round((count / row_count) * 100, 2) if row_count > 0 else 0.0
        for column, count in missing_values.items()
    }
    inferred_dtypes = {column: str(dtype) for column, dtype in df.dtypes.items()}
    unique_values = {
        column: int(df[column].nunique(dropna=True)) for column in df.columns
    }

    date_min: str | None = None
    date_max: str | None = None
    if "date" in df.columns and pd.api.types.is_datetime64_any_dtype(df["date"]):
        valid_dates = df["date"].dropna()
        if not valid_dates.empty:
            date_min = valid_dates.min().date().isoformat()
            date_max = valid_dates.max().date().isoformat()

    home_team_count = _count_unique_if_present(df, "home_team")
    away_team_count = _count_unique_if_present(df, "away_team")
    tournament_count = _count_unique_if_present(df, "tournament")

    return DatasetProfile(
        source_file=source_file,
        generated_at=datetime.now(),
        row_count=row_count,
        column_count=column_count,
        columns=columns,
        duplicate_row_count=duplicate_row_count,
        missing_values=missing_values,
        missing_percentages=missing_percentages,
        inferred_dtypes=inferred_dtypes,
        unique_values=unique_values,
        date_min=date_min,
        date_max=date_max,
        home_team_count=home_team_count,
        away_team_count=away_team_count,
        tournament_count=tournament_count,
        validation_errors=list(validation_result.errors) if validation_result else [],
        validation_warnings=list(validation_result.warnings) if validation_result else [],
    )


def profile_match_csv(path: Path) -> DatasetProfile:
    """Load, validate, and profile a match CSV file."""
    df, validation_result = load_and_validate_match_csv(path)
    return build_dataset_profile(
        df=df,
        source_file=path.name,
        validation_result=validation_result,
    )


def profile_to_markdown(profile: DatasetProfile) -> str:
    """Convert a dataset profile to a Markdown report."""
    lines: list[str] = [
        "# Data Profile Report",
        "",
        "## Dataset overview",
        "",
        f"- Source file: `{profile.source_file}`",
        f"- Generated at: `{profile.generated_at.isoformat(timespec='seconds')}`",
        f"- Rows: `{profile.row_count}`",
        f"- Columns: `{profile.column_count}`",
        f"- Duplicate rows: `{profile.duplicate_row_count}`",
        "",
        "Columns:",
        "",
    ]

    if profile.columns:
        for column in profile.columns:
            lines.append(f"- `{column}`")
    else:
        lines.append("- No columns found.")

    lines.extend(
        [
            "",
            "## Columns and inferred types",
            "",
            "| Column | Inferred dtype |",
            "|---|---|",
        ]
    )
    if profile.inferred_dtypes:
        for column, dtype in profile.inferred_dtypes.items():
            lines.append(f"| `{column}` | `{dtype}` |")
    else:
        lines.append("| No columns found | N/A |")

    lines.extend(
        [
            "",
            "## Missing values",
            "",
            "| Column | Missing count | Missing percentage |",
            "|---|---:|---:|",
        ]
    )
    if profile.missing_values:
        for column in profile.columns:
            lines.append(
                f"| `{column}` | {profile.missing_values[column]} | "
                f"{profile.missing_percentages[column]:.2f}% |"
            )
    else:
        lines.append("| No columns found | 0 | 0.00% |")

    lines.extend(
        [
            "",
            "## Cardinality",
            "",
            "| Column | Unique non-null values |",
            "|---|---:|",
        ]
    )
    if profile.unique_values:
        for column in profile.columns:
            lines.append(f"| `{column}` | {profile.unique_values[column]} |")
    else:
        lines.append("| No columns found | 0 |")

    lines.extend(
        [
            "",
            "## Date coverage",
            "",
            f"- Minimum date: `{profile.date_min}`" if profile.date_min else "- Minimum date: not available.",
            f"- Maximum date: `{profile.date_max}`" if profile.date_max else "- Maximum date: not available.",
            "",
            "## Match entities",
            "",
            _format_entity_line("Unique home teams", profile.home_team_count),
            _format_entity_line("Unique away teams", profile.away_team_count),
            _format_entity_line("Unique tournaments", profile.tournament_count),
            "",
            "## Validation errors",
            "",
        ]
    )

    if profile.validation_errors:
        for error in profile.validation_errors:
            lines.append(f"- {error}")
    else:
        lines.append("- No validation errors.")

    lines.extend(["", "## Validation warnings", ""])
    if profile.validation_warnings:
        for warning in profile.validation_warnings:
            lines.append(f"- {warning}")
    else:
        lines.append("- No validation warnings.")

    lines.extend(
        [
            "",
            "## Limitations",
            "",
            "- This report contains only aggregated characteristics and column names.",
            "- The report does not include raw row values from the dataset.",
            "- Profiling does not modify the source CSV file.",
            "- Profiling does not correct missing values, data types, team names, or match results.",
        ]
    )

    return "\n".join(lines) + "\n"


def save_profile_report(profile: DatasetProfile, output_path: Path) -> Path:
    """Save a Markdown profile report to disk."""
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(profile_to_markdown(profile), encoding="utf-8")
    return output_path


def default_profile_output_path(source_file: str) -> Path:
    """Build a safe default output path for a profile report."""
    source_name = Path(source_file).stem
    safe_name = re.sub(r"[^A-Za-z0-9_-]+", "_", source_name).strip("_")
    if not safe_name:
        safe_name = "dataset"
    return Path("reports") / "data_profiles" / f"{safe_name}_profile.md"


def _count_unique_if_present(df: pd.DataFrame, column: str) -> int | None:
    """Count unique non-null values for a column if it exists."""
    if column not in df.columns:
        return None
    return int(df[column].nunique(dropna=True))


def _format_entity_line(label: str, value: int | None) -> str:
    """Format a match-entity summary line for Markdown."""
    if value is None:
        return f"- {label}: not available."
    return f"- {label}: `{value}`"
