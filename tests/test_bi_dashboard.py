"""Checks for dashboard filter and KPI behavior on a small match slice."""

import pandas as pd
import pytest
from unittest.mock import MagicMock, patch
from sqlalchemy.exc import ProgrammingError
from dashboard.data import _read_matches_from_postgres

from dashboard.data import _prepare_matches, apply_global_filters, build_team_long, summarize_team, summarize_slice, apply_match_explorer_filters


def test_team_kpis_count_home_and_away_once():
    matches = _prepare_matches(pd.DataFrame([
        {"date": "2024-01-01", "home_team": "A", "away_team": "B", "home_score": 2,
         "away_score": 0, "tournament": "Cup", "country": "X", "neutral": False},
        {"date": "2024-02-01", "home_team": "B", "away_team": "A", "home_score": 1,
         "away_score": 1, "tournament": "Cup", "country": "Y", "neutral": True},
    ]))
    team_rows = build_team_long(matches)
    a = summarize_team(team_rows.loc[team_rows["team"] == "A"])
    assert a["matches"] == 2
    assert (a["wins"], a["draws"], a["losses"]) == (1, 1, 0)
    assert a["win_rate"] == 50.0
    assert (a["goals_for"], a["goals_against"]) == (3, 1)


def test_global_filters_combine_team_and_venue():
    matches = _prepare_matches(pd.DataFrame([
        {"date": "2024-01-01", "home_team": "A", "away_team": "B", "home_score": 2,
         "away_score": 0, "tournament": "Cup", "country": "X", "neutral": False},
        {"date": "2024-02-01", "home_team": "B", "away_team": "A", "home_score": 1,
         "away_score": 1, "tournament": "Cup", "country": "Y", "neutral": True},
    ]))
    filtered = apply_global_filters(matches, (2024, 2024), "Cup", "A", "All", "Only neutral")
    assert len(filtered) == 1
    assert filtered.iloc[0]["country"] == "Y"


def test_hosting_rate_excludes_neutral_unknown_and_unscored():
    matches = pd.DataFrame({
        "home_score": [2, 0, 3, None], "away_score": [0, 0, 0, None],
        "neutral": pd.array([False, True, None, False], dtype="boolean"),
    })
    kpis = summarize_slice(matches)
    assert kpis["hosted_matches"] == 1
    assert kpis["home_win_pct"] == 100.0
    assert kpis["draw_share_pct"] == pytest.approx(100 / 3)
    assert summarize_slice(matches.iloc[:0])["home_win_pct"] is None


def test_search_treats_brackets_as_literal_text():
    matches = _prepare_matches(pd.DataFrame([{
        "date": "2024-01-01", "home_team": "A [test]", "away_team": "B",
        "home_score": 1, "away_score": 0, "neutral": False,
    }]))
    result = apply_match_explorer_filters(matches, "[", 0, False, False)
    assert len(result) == 1


def test_postgres_reads_view_and_reports_source():
    engine = MagicMock()
    with patch("dashboard.data._build_database_url", return_value="configured"), patch(
        "sqlalchemy.create_engine", return_value=engine
    ), patch("dashboard.data.pd.read_sql", return_value=pd.DataFrame()) as read:
        _, source = _read_matches_from_postgres()
        query = str(read.call_args.args[0])
        assert "FROM bi_match_facts" in query
        assert "match_date" not in query
        assert source == "PostgreSQL view: bi_match_facts"
    engine.dispose.assert_called_once()


def test_missing_view_rolls_back_before_legacy_query():
    engine = MagicMock()
    connection = engine.connect.return_value.__enter__.return_value
    original = Exception("undefined relation")
    original.sqlstate = "42P01"
    with patch("dashboard.data._build_database_url", return_value="configured"), patch(
        "sqlalchemy.create_engine", return_value=engine
    ), patch("dashboard.data.pd.read_sql", side_effect=[
        ProgrammingError("query", {}, original), pd.DataFrame()
    ]) as read:
        _, source = _read_matches_from_postgres()
        connection.rollback.assert_called_once()
        assert "FROM matches" in str(read.call_args.args[0])
        assert source == "PostgreSQL table: matches"
    engine.dispose.assert_called_once()
