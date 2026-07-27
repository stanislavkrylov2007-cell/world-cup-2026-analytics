"""Command line utilities for the project."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from world_cup_analytics.config import load_config
from world_cup_analytics.database.load_matches import _create_engine, _sql_text, load_matches_dataframe
from world_cup_analytics.data.loader import load_and_validate_match_csv
from world_cup_analytics.data.profiling import (
    default_profile_output_path,
    profile_match_csv,
    save_profile_report,
)
from world_cup_analytics.data.transform import (
    default_transformation_report_path,
    save_transformation_report,
    transform_match_csv,
)


def check_config_command() -> None:
    """Verify that the package imports and the configuration can be loaded."""
    config = load_config()
    print("World Cup 2026 Analytics: configuration loaded successfully.")
    print(f"Environment: {config.app_env}")
    print(f"Database host: {config.db_host}")
    print(f"Database port: {config.db_port}")
    print(f"Database name: {config.db_name}")
    print(f"Database user: {config.db_user}")


def validate_data_command() -> None:
    """Validate a CSV file with match data."""
    parser = argparse.ArgumentParser(
        description="Validate a CSV file with football match data."
    )
    parser.add_argument("path", type=Path, help="Path to the CSV file.")
    args = parser.parse_args()

    try:
        _, result = load_and_validate_match_csv(args.path)
    except (FileNotFoundError, NotADirectoryError, ValueError) as error:
        print(f"Validation failed: {error}")
        raise SystemExit(1) from error

    print(f"Rows: {result.row_count}")
    print(f"Columns: {result.column_count}")

    if result.errors:
        print("Errors:")
        for error in result.errors:
            print(f"- {error}")

    if result.warnings:
        print("Warnings:")
        for warning in result.warnings:
            print(f"- {warning}")

    if result.is_valid:
        print("Validation passed.")
        raise SystemExit(0)

    print("Validation failed due to data errors.")
    raise SystemExit(1)


def profile_data_command() -> None:
    """Build and save a Markdown profile for a CSV file."""
    parser = argparse.ArgumentParser(
        description="Profile a CSV file with football match data."
    )
    parser.add_argument("path", type=Path, help="Path to the CSV file.")
    args = parser.parse_args()

    try:
        profile = profile_match_csv(args.path)
        output_path = save_profile_report(
            profile=profile,
            output_path=default_profile_output_path(args.path.name),
        )
    except (FileNotFoundError, NotADirectoryError, ValueError, OSError) as error:
        print(f"Profiling failed: {error}")
        raise SystemExit(1) from error

    print(f"Profile report saved to: {output_path}")
    print(f"Rows: {profile.row_count}")
    print(f"Columns: {profile.column_count}")
    print(f"Duplicate rows: {profile.duplicate_row_count}")
    print(f"Validation errors: {len(profile.validation_errors)}")
    print(f"Validation warnings: {len(profile.validation_warnings)}")
    raise SystemExit(0)


def transform_data_command() -> None:
    """Transform a source CSV file into the project interim contract."""
    parser = argparse.ArgumentParser(
        description="Transform a CSV file into the project interim dataset."
    )
    parser.add_argument("path", type=Path, help="Path to the source CSV file.")
    parser.add_argument(
        "--mapping",
        type=Path,
        required=True,
        help="Path to the column mapping TOML file.",
    )
    parser.add_argument(
        "--output",
        type=Path,
        required=True,
        help="Path to the standardized output CSV file.",
    )
    parser.add_argument(
        "--overwrite",
        action="store_true",
        help="Overwrite the output file if it already exists.",
    )
    args = parser.parse_args()

    try:
        result = transform_match_csv(
            source_path=args.path,
            mapping_path=args.mapping,
            output_path=args.output,
            overwrite=args.overwrite,
        )
        report_path = save_transformation_report(
            result=result,
            output_path=default_transformation_report_path(args.output),
        )
    except (FileNotFoundError, NotADirectoryError, ValueError, OSError) as error:
        print(f"Transformation failed: {error}")
        raise SystemExit(1) from error

    print(f"Transformation report saved to: {report_path}")
    print(f"Input rows: {result.input_row_count}")
    print(f"Output rows: {result.output_row_count}")
    print(f"Added columns: {len(result.added_columns)}")
    print(f"Dropped columns: {len(result.dropped_columns)}")
    print(f"Warnings: {len(result.warnings)}")
    print(f"Errors: {len(result.errors)}")

    if result.is_successful:
        print(f"Standardized dataset saved to: {result.output_file}")
        raise SystemExit(0)

    print("Transformation failed. See the saved report for details.")
    raise SystemExit(1)


def load_postgres_command() -> None:
    """Load a standardized CSV file into PostgreSQL."""
    parser = argparse.ArgumentParser(
        description="Load a standardized match CSV file into PostgreSQL."
    )
    parser.add_argument("path", type=Path, help="Path to the standardized CSV file.")
    parser.add_argument(
        "--replace",
        action="store_true",
        help="Replace rows for the same source_file before loading.",
    )
    args = parser.parse_args()

    try:
        config = load_config()
        df, validation_result = load_and_validate_match_csv(args.path)
        if validation_result.errors:
            joined_errors = "; ".join(validation_result.errors)
            raise ValueError(
                "Standardized CSV is not valid for database loading: "
                f"{joined_errors}"
            )

        engine = _create_engine(config.database_url)
        source_file = args.path.name

        with engine.connect() as connection:
            loaded_row_count = load_matches_dataframe(
                connection=connection,
                df=df,
                source_file=source_file,
                replace=args.replace,
            )
            row_count_in_table = int(
                connection.execute(
                    _sql_text(
                        "SELECT COUNT(*) FROM matches WHERE source_file = :source_file"
                    ),
                    {"source_file": source_file},
                ).scalar_one()
            )
    except (FileNotFoundError, NotADirectoryError, ValueError, OSError, Exception) as error:
        print(f"PostgreSQL load failed: {error}")
        raise SystemExit(1) from error

    print("PostgreSQL load completed successfully.")
    print(f"Database: {config.db_name}")
    print(f"Source file: {source_file}")
    print(f"Loaded rows: {loaded_row_count}")
    print(f"Rows in table for source_file: {row_count_in_table}")
    raise SystemExit(0)


if __name__ == "__main__":
    if len(sys.argv) > 1:
        validate_data_command()
    check_config_command()
