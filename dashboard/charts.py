"""Plotly chart helpers for the Streamlit dashboard."""

from __future__ import annotations

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

COLORWAY = ["#0B6E4F", "#F4A259", "#5C677D", "#5B8E7D", "#D95D39"]
LAYOUT = {
    "template": "plotly_white",
    "colorway": COLORWAY,
    "margin": {"l": 40, "r": 20, "t": 60, "b": 40},
    "height": 420,
    "legend": {"orientation": "h", "yanchor": "bottom", "y": 1.02, "x": 0},
}


def _apply_layout(fig: go.Figure, height: int = 420) -> go.Figure:
    """Apply a consistent visual style to figures."""
    layout_config = dict(LAYOUT)
    layout_config["height"] = height
    fig.update_layout(**layout_config)
    fig.update_yaxes(rangemode="tozero")
    return fig


def matches_by_year_chart(yearly_df: pd.DataFrame) -> go.Figure:
    """Build a matches-by-year line chart."""
    fig = px.line(
        yearly_df,
        x="year",
        y="matches",
        title="International Matches by Year",
        labels={"year": "Year", "matches": "Matches"},
        markers=False,
    )
    return _apply_layout(fig)


def metric_trend_chart(
    yearly_df: pd.DataFrame,
    metric: str,
    title: str,
    y_label: str,
) -> go.Figure:
    """Build a generic yearly trend chart."""
    fig = px.line(
        yearly_df,
        x="year",
        y=metric,
        title=title,
        labels={"year": "Year", metric: y_label},
    )
    return _apply_layout(fig)


def outcome_distribution_chart(outcome_df: pd.DataFrame) -> go.Figure:
    """Build a bar chart for match outcomes."""
    fig = px.bar(
        outcome_df,
        x="result",
        y="share_pct",
        color="result",
        title="Match Outcome Distribution",
        labels={"result": "Result", "share_pct": "Share of matches, %"},
        text="share_pct",
    )
    fig.update_traces(texttemplate="%{text:.1f}%", textposition="outside")
    fig.update_layout(showlegend=False)
    return _apply_layout(fig)


def top_teams_chart(
    teams_df: pd.DataFrame,
    metric: str,
    title: str,
    x_label: str,
    limit: int = 15,
) -> go.Figure:
    """Build a horizontal ranking chart for teams."""
    chart_df = teams_df.head(limit).sort_values(metric, ascending=True)
    fig = px.bar(
        chart_df,
        x=metric,
        y="team",
        orientation="h",
        title=title,
        labels={metric: x_label, "team": "Team"},
        text=metric,
    )
    fig.update_traces(texttemplate="%{text:.2f}" if "rate" in metric else "%{text}")
    return _apply_layout(fig, height=520)


def goals_histogram_chart(matches_df: pd.DataFrame) -> go.Figure:
    """Build a histogram of total goals."""
    fig = px.histogram(
        matches_df,
        x="total_goals",
        nbins=15,
        title="Distribution of Total Goals",
        labels={"total_goals": "Total goals in a match", "count": "Matches"},
    )
    return _apply_layout(fig)


def venue_comparison_chart(comparison_df: pd.DataFrame) -> go.Figure:
    """Build a grouped bar chart comparing venue types."""
    fig = px.bar(
        comparison_df,
        x="venue_type",
        y="share_pct",
        color="result",
        barmode="group",
        title="Home, Draw, and Away Shares by Venue Type",
        labels={
            "venue_type": "Venue type",
            "share_pct": "Share of matches, %",
            "result": "Result",
        },
        text="share_pct",
    )
    fig.update_traces(texttemplate="%{text:.1f}%", textposition="outside")
    return _apply_layout(fig)


def top_tournaments_chart(tournament_df: pd.DataFrame, limit: int = 20) -> go.Figure:
    """Build a horizontal ranking chart for tournaments."""
    chart_df = tournament_df.head(limit).sort_values("matches", ascending=True)
    fig = px.bar(
        chart_df,
        x="matches",
        y="tournament",
        orientation="h",
        title="Top Tournaments by Match Count",
        labels={"matches": "Matches", "tournament": "Tournament"},
        text="matches",
    )
    return _apply_layout(fig, height=620)


def top_countries_chart(country_df: pd.DataFrame, limit: int = 15) -> go.Figure:
    """Build a horizontal ranking chart for host countries."""
    chart_df = country_df.head(limit).sort_values("matches", ascending=True)
    fig = px.bar(
        chart_df,
        x="matches",
        y="country",
        orientation="h",
        title="Top Host Countries by Match Count",
        labels={"matches": "Matches", "country": "Country"},
        text="matches",
    )
    return _apply_layout(fig, height=520)


def team_results_stacked_chart(yearly_df: pd.DataFrame) -> go.Figure:
    """Build a stacked yearly results chart for a selected team."""
    long_df = yearly_df.melt(
        id_vars="year",
        value_vars=["wins", "draws", "losses"],
        var_name="result_type",
        value_name="result_count",
    )
    fig = px.bar(
        long_df,
        x="year",
        y="result_count",
        color="result_type",
        barmode="stack",
        title="Team Results by Year",
        labels={
            "year": "Year",
            "result_count": "Matches",
            "result_type": "Result type",
        },
    )
    return _apply_layout(fig)


def top_opponents_chart(opponents_df: pd.DataFrame) -> go.Figure:
    """Build a chart for a team's most common opponents."""
    chart_df = opponents_df.sort_values("matches", ascending=True)
    fig = px.bar(
        chart_df,
        x="matches",
        y="opponent",
        orientation="h",
        title="Top Opponents by Match Count",
        labels={"matches": "Matches", "opponent": "Opponent"},
        text="matches",
    )
    return _apply_layout(fig, height=420)


def tournament_yearly_chart(yearly_df: pd.DataFrame) -> go.Figure:
    """Build a yearly volume chart for the selected tournament."""
    fig = px.line(
        yearly_df,
        x="year",
        y="matches",
        title="Tournament Matches by Year",
        labels={"year": "Year", "matches": "Matches"},
    )
    return _apply_layout(fig)
