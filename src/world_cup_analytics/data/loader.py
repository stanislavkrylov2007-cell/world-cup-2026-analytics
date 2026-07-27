"""CSV loading helpers for match data."""

from __future__ import annotations

from pathlib import Path

import pandas as pd

from world_cup_analytics.data.validation import ValidationResult, validate_match_dataframe


def find_csv_files(raw_dir: Path) -> list[Path]:
    """Return sorted CSV files from the provided directory."""
    if not raw_dir.exists():
        raise FileNotFoundError(f"Directory does not exist: {raw_dir}")
    if not raw_dir.is_dir():
        raise NotADirectoryError(f"Path is not a directory: {raw_dir}")
    return sorted(path for path in raw_dir.iterdir() if path.is_file() and path.suffix.lower() == ".csv")


def load_match_csv(path: Path) -> pd.DataFrame:
    """Load a CSV file, normalize column names, and trim string values."""
    if not path.exists():
        raise FileNotFoundError(f"CSV file does not exist: {path}")
    if path.suffix.lower() != ".csv":
        raise ValueError(f"Expected a .csv file, got: {path.name}")

    try:
        df = pd.read_csv(path, encoding="utf-8")
    except UnicodeDecodeError as error:
        raise ValueError(
            "Could not read the CSV file as UTF-8. Please check the file encoding."
        ) from error

    df = df.copy()
    df.columns = [column.strip().lower() for column in df.columns]

    for column in df.select_dtypes(include=["object", "string"]).columns:
        df[column] = df[column].map(lambda value: value.strip() if isinstance(value, str) else value)

    if "date" in df.columns:
        df["date"] = pd.to_datetime(df["date"], errors="coerce")

    return df


def load_and_validate_match_csv(path: Path) -> tuple[pd.DataFrame, ValidationResult]:
    """Load a CSV file and validate its content."""
    df = load_match_csv(path)
    validation_result = validate_match_dataframe(df)
    return df, validation_result
