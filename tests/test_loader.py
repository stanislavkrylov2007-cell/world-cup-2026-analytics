"""Tests for CSV loading helpers."""

from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from world_cup_analytics.data.loader import (
    find_csv_files,
    load_and_validate_match_csv,
    load_match_csv,
)


VALID_CSV_CONTENT = """date,home_team,away_team,home_score,away_score,tournament,city,country,neutral
2024-01-01,Alpha United,Gamma Rovers,1,0,Test Cup,North City,Exampland,false
2024-01-02,Beta City,Delta Stars,2,2,Test Cup,South City,Exampland,true
"""


class TestLoader(unittest.TestCase):
    """Test cases for loader utilities."""

    def test_load_valid_temporary_csv(self) -> None:
        """A valid temporary CSV file should be loaded and validated."""
        with tempfile.TemporaryDirectory() as temp_dir:
            path = Path(temp_dir) / "matches.csv"
            path.write_text(VALID_CSV_CONTENT, encoding="utf-8")

            df, result = load_and_validate_match_csv(path)

            self.assertEqual(df.shape, (2, 9))
            self.assertTrue(result.is_valid)

    def test_find_csv_files(self) -> None:
        """The loader should find only CSV files."""
        with tempfile.TemporaryDirectory() as temp_dir:
            raw_dir = Path(temp_dir)
            (raw_dir / "a.csv").write_text("x\n1\n", encoding="utf-8")
            (raw_dir / "b.txt").write_text("x\n1\n", encoding="utf-8")
            (raw_dir / "c.CSV").write_text("x\n1\n", encoding="utf-8")

            result = find_csv_files(raw_dir)

            self.assertEqual([path.name for path in result], ["a.csv", "c.CSV"])

    def test_missing_file(self) -> None:
        """A missing file should raise FileNotFoundError."""
        with self.assertRaises(FileNotFoundError):
            load_match_csv(Path("missing.csv"))

    def test_invalid_extension(self) -> None:
        """A non-CSV file should raise ValueError."""
        with tempfile.TemporaryDirectory() as temp_dir:
            path = Path(temp_dir) / "matches.txt"
            path.write_text("test", encoding="utf-8")

            with self.assertRaisesRegex(ValueError, ".csv"):
                load_match_csv(path)


if __name__ == "__main__":
    unittest.main()
