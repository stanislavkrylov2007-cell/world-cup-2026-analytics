"""Transformation helpers for standardizing match CSV files."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import os
import tempfile
import tomllib

import pandas as pd

from world_cup_analytics.data.loader import load_match_csv
from world_cup_analytics.data.validation import (
    OPTIONAL_COLUMNS,
    REQUIRED_COLUMNS,
    validate_match_dataframe,
)

ALL_CONTRACT_COLUMNS: tuple[str, ...] = REQUIRED_COLUMNS + OPTIONAL_COLUMNS
TRUE_NEUTRAL_VALUES = {"true", "1", "yes", "y", "neutral"}
FALSE_NEUTRAL_VALUES = {"false", "0", "no", "n", "home"}


@dataclass(frozen=True)
class TransformationResult:
    """Result of transforming a source dataset into the project contract."""

    source_file: str
    output_file: str | None
    input_row_count: int
    output_row_count: int
    input_columns: list[str]
    output_columns: list[str]
    renamed_columns: dict[str, str]
    added_columns: list[str]
    dropped_columns: list[str]
    type_conversions: list[str]
    warnings: list[str]
    errors: list[str]
    is_successful: bool


def load_column_mapping(path: Path) -> dict[str, str]:
    """Load a column mapping from a TOML file."""
    if not path.exists():
        raise FileNotFoundError(f"Mapping file does not exist: {path}")
    if path.suffix.lower() != ".toml":
        raise ValueError(f"Expected a .toml mapping file, got: {path.name}")

    try:
        config = tomllib.loads(path.read_text(encoding="utf-8"))
    except tomllib.TOMLDecodeError as error:
        raise ValueError(f"Could not parse TOML mapping file: {path}") from error

    source_columns = config.get("source_columns")
    if not isinstance(source_columns, dict):
        raise ValueError("Mapping file must contain a [source_columns] table.")

    mapping: dict[str, str] = {}
    for key, value in source_columns.items():
        if not isinstance(key, str) or not isinstance(value, str):
            raise ValueError("All mapping keys and values must be strings.")
        mapping[key.strip()] = value.strip().lower()

    return mapping


def validate_column_mapping(df: pd.DataFrame, mapping: dict[str, str]) -> list[str]:
    """Validate that a column mapping is complete and usable."""
    errors: list[str] = []

    unknown_targets = [key for key in mapping if key not in ALL_CONTRACT_COLUMNS]
    if unknown_targets:
        errors.append(
            "Mapping contains unknown target fields: "
            f"{', '.join(sorted(unknown_targets))}."
        )

    missing_required_targets = [
        column for column in REQUIRED_COLUMNS if column not in mapping
    ]
    if missing_required_targets:
        errors.append(
            "Mapping is missing required target fields: "
            f"{', '.join(missing_required_targets)}."
        )

    duplicate_source_columns = _find_duplicate_source_columns(mapping)
    if duplicate_source_columns:
        errors.append(
            "Mapping reuses the same source column for multiple target fields: "
            f"{', '.join(duplicate_source_columns)}."
        )

    for target_column, source_column in mapping.items():
        if source_column not in df.columns:
            errors.append(
                f"Source column '{source_column}' for target '{target_column}' was not found."
            )

    return errors


def standardize_neutral_series(series: pd.Series) -> tuple[pd.Series, list[str]]:
    """Normalize neutral-field values to nullable boolean values."""
    standardized = pd.Series(pd.NA, index=series.index, dtype="boolean")
    warnings: list[str] = []

    known_mask = pd.Series(False, index=series.index)
    missing_mask = series.isna()

    normalized_strings = series.astype("string").str.strip().str.lower()
    true_mask = normalized_strings.isin(TRUE_NEUTRAL_VALUES)
    false_mask = normalized_strings.isin(FALSE_NEUTRAL_VALUES)

    standardized.loc[true_mask] = True
    standardized.loc[false_mask] = False
    known_mask = true_mask | false_mask | missing_mask

    unknown_count = int((~known_mask).sum())
    if unknown_count > 0:
        warnings.append(
            "Column 'neutral' contains unknown values. "
            f"{unknown_count} value(s) were converted to missing."
        )

    return standardized, warnings


def transform_matches_dataframe(
    df: pd.DataFrame,
    mapping: dict[str, str],
) -> tuple[pd.DataFrame, TransformationResult]:
    """Transform a loaded DataFrame to the internal project contract."""
    input_df = df.copy(deep=True)
    errors = validate_column_mapping(input_df, mapping)
    warnings: list[str] = []
    type_conversions: list[str] = []
    added_columns: list[str] = []
    input_columns = list(input_df.columns)
    renamed_columns = {source: target for target, source in mapping.items()}
    dropped_columns = sorted(
        column for column in input_columns if column not in set(mapping.values())
    )

    if errors:
        result = TransformationResult(
            source_file="",
            output_file=None,
            input_row_count=len(input_df.index),
            output_row_count=0,
            input_columns=input_columns,
            output_columns=[],
            renamed_columns=renamed_columns,
            added_columns=added_columns,
            dropped_columns=dropped_columns,
            type_conversions=type_conversions,
            warnings=warnings,
            errors=errors,
            is_successful=False,
        )
        return pd.DataFrame(), result

    selected_source_columns = [mapping[column] for column in mapping]
    transformed_df = input_df.loc[:, selected_source_columns].copy()
    transformed_df = transformed_df.rename(columns=renamed_columns)

    for column in transformed_df.select_dtypes(include=["object", "string"]).columns:
        transformed_df[column] = transformed_df[column].map(
            lambda value: value.strip() if isinstance(value, str) else value
        )

    for optional_column in OPTIONAL_COLUMNS:
        if optional_column not in transformed_df.columns:
            transformed_df[optional_column] = pd.NA
            added_columns.append(optional_column)

    if "date" in transformed_df.columns:
        transformed_df["date"] = pd.to_datetime(transformed_df["date"], errors="coerce")
        type_conversions.append("Converted 'date' to datetime.")

    score_errors, score_conversion_messages = _convert_score_columns(transformed_df)
    errors.extend(score_errors)
    type_conversions.extend(score_conversion_messages)

    if "neutral" in transformed_df.columns:
        transformed_df["neutral"], neutral_warnings = standardize_neutral_series(
            transformed_df["neutral"]
        )
        warnings.extend(neutral_warnings)
        type_conversions.append("Standardized 'neutral' to nullable boolean.")

    transformed_df = transformed_df.loc[:, list(ALL_CONTRACT_COLUMNS)]

    validation_result = validate_match_dataframe(transformed_df)
    errors.extend(validation_result.errors)
    warnings.extend(validation_result.warnings)

    result = TransformationResult(
        source_file="",
        output_file=None,
        input_row_count=len(input_df.index),
        output_row_count=len(transformed_df.index),
        input_columns=input_columns,
        output_columns=list(transformed_df.columns),
        renamed_columns=renamed_columns,
        added_columns=added_columns,
        dropped_columns=dropped_columns,
        type_conversions=type_conversions,
        warnings=_unique_preserve_order(warnings),
        errors=_unique_preserve_order(errors),
        is_successful=not errors,
    )
    return transformed_df, result


def transform_match_csv(
    source_path: Path,
    mapping_path: Path,
    output_path: Path,
    overwrite: bool = False,
) -> TransformationResult:
    """Transform a source CSV file into a standardized interim dataset."""
    df = load_match_csv(source_path)
    mapping = load_column_mapping(mapping_path)
    transformed_df, result = transform_matches_dataframe(df, mapping)

    errors = list(result.errors)
    warnings = list(result.warnings)

    if output_path.exists() and not overwrite:
        errors.append(
            f"Output file already exists: {output_path}. Use --overwrite to replace it."
        )

    is_successful = not errors
    output_file = None
    if is_successful:
        _atomic_write_csv(transformed_df, output_path)
        output_file = str(output_path)

    return TransformationResult(
        source_file=str(source_path),
        output_file=output_file,
        input_row_count=result.input_row_count,
        output_row_count=result.output_row_count,
        input_columns=result.input_columns,
        output_columns=result.output_columns,
        renamed_columns=result.renamed_columns,
        added_columns=result.added_columns,
        dropped_columns=result.dropped_columns,
        type_conversions=result.type_conversions,
        warnings=warnings,
        errors=errors,
        is_successful=is_successful,
    )


def transformation_result_to_markdown(result: TransformationResult) -> str:
    """Convert a transformation result to a Markdown report."""
    lines: list[str] = [
        "# Transformation Report",
        "",
        "## Overview",
        "",
        f"- Source file: `{result.source_file}`",
        f"- Output file: `{result.output_file}`" if result.output_file else "- Output file: not created.",
        f"- Input rows: `{result.input_row_count}`",
        f"- Output rows: `{result.output_row_count}`",
        f"- Successful: `{result.is_successful}`",
        "",
        "## Columns",
        "",
        f"- Input columns: `{', '.join(result.input_columns)}`" if result.input_columns else "- Input columns: none.",
        f"- Output columns: `{', '.join(result.output_columns)}`" if result.output_columns else "- Output columns: none.",
        "",
        "## Renamed columns",
        "",
    ]

    if result.renamed_columns:
        for source, target in result.renamed_columns.items():
            lines.append(f"- `{source}` -> `{target}`")
    else:
        lines.append("- No renamed columns.")

    lines.extend(["", "## Added columns", ""])
    if result.added_columns:
        for column in result.added_columns:
            lines.append(f"- `{column}` added with missing values.")
    else:
        lines.append("- No added columns.")

    lines.extend(["", "## Dropped columns", ""])
    if result.dropped_columns:
        for column in result.dropped_columns:
            lines.append(f"- `{column}`")
    else:
        lines.append("- No dropped columns.")

    lines.extend(["", "## Type conversions", ""])
    if result.type_conversions:
        for conversion in result.type_conversions:
            lines.append(f"- {conversion}")
    else:
        lines.append("- No type conversions recorded.")

    lines.extend(["", "## Errors", ""])
    if result.errors:
        for error in result.errors:
            lines.append(f"- {error}")
    else:
        lines.append("- No errors.")

    lines.extend(["", "## Warnings", ""])
    if result.warnings:
        for warning in result.warnings:
            lines.append(f"- {warning}")
    else:
        lines.append("- No warnings.")

    lines.extend(
        [
            "",
            "## Limitations",
            "",
            "- The report contains only schema-level and aggregated transformation details.",
            "- The report does not include raw row values from the source dataset.",
            "- Team names are not normalized at this stage.",
            "- Invalid rows are not deleted or repaired automatically.",
        ]
    )

    return "\n".join(lines) + "\n"


def save_transformation_report(
    result: TransformationResult,
    output_path: Path,
) -> Path:
    """Save a transformation report to disk."""
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(
        transformation_result_to_markdown(result),
        encoding="utf-8",
    )
    return output_path


def default_transformation_report_path(output_path: Path) -> Path:
    """Build a default report path for a transformation result."""
    return Path("reports") / "transformations" / f"{output_path.stem}_report.md"


def _convert_score_columns(df: pd.DataFrame) -> tuple[list[str], list[str]]:
    """Convert score columns to nullable integers when possible."""
    errors: list[str] = []
    conversions: list[str] = []

    for column in ("home_score", "away_score"):
        if column not in df.columns:
            continue

        numeric_values = pd.to_numeric(df[column], errors="coerce")
        invalid_mask = df[column].notna() & numeric_values.isna()
        fractional_mask = numeric_values.notna() & (numeric_values % 1 != 0)

        if invalid_mask.any() or fractional_mask.any():
            errors.append(
                f"Column '{column}' cannot be safely converted to integer scores."
            )
            continue

        df[column] = numeric_values.astype("Int64")
        conversions.append(f"Converted '{column}' to nullable integer.")

    return errors, conversions


def _find_duplicate_source_columns(mapping: dict[str, str]) -> list[str]:
    """Find source columns that are mapped more than once."""
    seen: dict[str, int] = {}
    duplicates: list[str] = []
    for source_column in mapping.values():
        seen[source_column] = seen.get(source_column, 0) + 1
        if seen[source_column] == 2:
            duplicates.append(source_column)
    return sorted(duplicates)


def _unique_preserve_order(values: list[str]) -> list[str]:
    """Return a list with duplicates removed while keeping the original order."""
    seen: set[str] = set()
    unique_values: list[str] = []
    for value in values:
        if value not in seen:
            seen.add(value)
            unique_values.append(value)
    return unique_values


def _atomic_write_csv(df: pd.DataFrame, output_path: Path) -> None:
    """Atomically write a CSV file to disk."""
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile(
        mode="w",
        encoding="utf-8",
        newline="",
        delete=False,
        dir=output_path.parent,
        suffix=".tmp",
    ) as temp_file:
        temp_path = Path(temp_file.name)

    try:
        df.to_csv(temp_path, index=False)
        os.replace(temp_path, output_path)
    finally:
        if temp_path.exists():
            temp_path.unlink()
