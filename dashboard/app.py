"""Streamlit dashboard for World Cup 2026 Analytics."""

from __future__ import annotations

from io import StringIO

import pandas as pd
import streamlit as st

from dashboard.charts import (
    matches_by_year_chart,
    metric_trend_chart,
    outcome_distribution_chart,
    team_results_stacked_chart,
    top_opponents_chart,
    top_teams_chart,
    top_tournaments_chart,
    tournament_yearly_chart,
    venue_comparison_chart,
)
from dashboard.data import (
    apply_global_filters,
    apply_match_explorer_filters,
    biggest_wins,
    build_team_long,
    get_filter_options,
    latest_team_matches,
    load_matches,
    summarize_team,
    top_team_opponents,
    tournament_team_summary,
    yearly_team_results,
)

st.set_page_config(
    page_title="World Cup 2026 Analytics",
    layout="wide",
    initial_sidebar_state="expanded",
)

FILTER_KEYS = [
    "year_range",
    "tournament_filter",
    "team_filter",
    "country_filter",
    "venue_filter",
]


def reset_global_filters() -> None:
    """Reset sidebar filters to their default values."""
    for key in FILTER_KEYS:
        st.session_state.pop(key, None)


def format_int(value: int) -> str:
    """Format integers for display."""
    return f"{int(value):,}"


def format_float(value: float, digits: int = 2) -> str:
    """Format floating-point values for display."""
    return f"{value:,.{digits}f}"


def show_empty_state(message: str) -> None:
    """Render a consistent empty-state message."""
    st.info(message)


@st.cache_data(show_spinner=False)
def build_overview_insights(matches_df: pd.DataFrame) -> list[str]:
    """Create a short set of data-driven overview insights."""
    if matches_df.empty:
        return []

    top_year = (
        matches_df.groupby("year", as_index=False)
        .size()
        .rename(columns={"size": "matches"})
        .sort_values("matches", ascending=False)
        .iloc[0]
    )
    top_tournament = matches_df["tournament"].value_counts().idxmax()
    top_tournament_count = int(matches_df["tournament"].value_counts().max())
    home_win_share = (
        (matches_df["result"] == "Home win").mean() * 100 if len(matches_df.index) else 0.0
    )
    avg_goals = matches_df["total_goals"].mean()
    neutral_share = (
        matches_df["neutral"].fillna(False).astype(bool).mean() * 100
        if "neutral" in matches_df.columns
        else 0.0
    )

    return [
        f"Peak activity comes in {int(top_year['year'])} with {format_int(int(top_year['matches']))} matches.",
        f"The most frequent tournament in the current slice is {top_tournament} with {format_int(top_tournament_count)} matches.",
        f"Home wins account for {format_float(home_win_share, 1)}% of filtered matches.",
        f"Average scoring is {format_float(avg_goals, 2)} goals per match.",
        f"Neutral-venue matches make up {format_float(neutral_share, 1)}% of the current selection.",
    ]


@st.cache_data(show_spinner=False)
def build_yearly_trends(matches_df: pd.DataFrame) -> pd.DataFrame:
    """Aggregate yearly trends for the trends tab."""
    non_neutral_df = matches_df.loc[matches_df["neutral"] == False]  # noqa: E712

    yearly_df = (
        matches_df.groupby("year", as_index=False)
        .agg(
            matches=("date", "size"),
            avg_goals=("total_goals", "mean"),
            draw_share=("result", lambda values: (values == "Draw").mean() * 100),
        )
        .sort_values("year")
    )

    home_non_neutral_df = (
        non_neutral_df.groupby("year", as_index=False)
        .agg(
            home_win_share=(
                "result",
                lambda values: (values == "Home win").mean() * 100,
            )
        )
        .sort_values("year")
    )

    return yearly_df.merge(home_non_neutral_df, on="year", how="left")


def apply_smoothing(yearly_df: pd.DataFrame, window: int) -> pd.DataFrame:
    """Apply rolling mean smoothing without inventing early values."""
    smoothed_df = yearly_df.copy()
    metrics = ["matches", "avg_goals", "draw_share", "home_win_share"]

    if window <= 1:
        return smoothed_df

    for column in metrics:
        smoothed_df[column] = (
            smoothed_df[column].rolling(window=window, min_periods=window).mean()
        )

    return smoothed_df


@st.cache_data(show_spinner=False)
def build_team_ranking(matches_df: pd.DataFrame) -> pd.DataFrame:
    """Build a team ranking table from the filtered dataset."""
    team_df = build_team_long(matches_df)
    ranking_df = (
        team_df.groupby("team", as_index=False)
        .agg(
            matches=("team", "size"),
            wins=("is_win", "sum"),
            draws=("is_draw", "sum"),
            losses=("is_loss", "sum"),
            goals_for=("goals_for", "sum"),
            goals_against=("goals_against", "sum"),
        )
        .sort_values(["wins", "matches", "team"], ascending=[False, False, True])
    )
    ranking_df["goal_difference"] = (
        ranking_df["goals_for"] - ranking_df["goals_against"]
    )
    ranking_df["win_rate"] = ranking_df["wins"] / ranking_df["matches"] * 100
    ranking_df["avg_goals_for"] = ranking_df["goals_for"] / ranking_df["matches"]
    return ranking_df


@st.cache_data(show_spinner=False)
def build_outcome_distribution(matches_df: pd.DataFrame) -> pd.DataFrame:
    """Prepare outcome shares for plotting."""
    distribution_df = (
        matches_df["result"]
        .value_counts(normalize=True)
        .rename_axis("result")
        .reset_index(name="share")
    )
    distribution_df["share_pct"] = distribution_df["share"] * 100
    order = pd.CategoricalDtype(["Home win", "Draw", "Away win"], ordered=True)
    distribution_df["result"] = distribution_df["result"].astype(order)
    return distribution_df.sort_values("result")


@st.cache_data(show_spinner=False)
def build_venue_comparison(matches_df: pd.DataFrame) -> pd.DataFrame:
    """Prepare venue comparison data for plotting."""
    comparison_df = matches_df.copy()
    comparison_df["venue_type"] = comparison_df["neutral"].map(
        {True: "Neutral", False: "Non-neutral"}
    )
    comparison_df["venue_type"] = comparison_df["venue_type"].fillna("Unknown")

    grouped_df = (
        comparison_df.groupby(["venue_type", "result"], as_index=False)
        .size()
        .rename(columns={"size": "matches"})
    )
    totals_df = grouped_df.groupby("venue_type", as_index=False)["matches"].sum()
    totals_df = totals_df.rename(columns={"matches": "venue_matches"})
    grouped_df = grouped_df.merge(totals_df, on="venue_type", how="left")
    grouped_df["share_pct"] = grouped_df["matches"] / grouped_df["venue_matches"] * 100
    return grouped_df


st.title("World Cup 2026 Analytics")
st.caption(
    "Interactive dashboard for historical international football results. "
    "Data source priority: PostgreSQL table `matches` -> standardized CSV fallback."
)

matches_df, data_source, load_message = load_matches()

if matches_df is None:
    st.error(load_message or "No data source is available.")
    st.stop()

if load_message:
    st.warning(load_message)

st.success(f"Loaded data source: {data_source}")

filter_options = get_filter_options(matches_df)
default_year_range = (
    filter_options["year_min"],
    filter_options["year_max"],
)

with st.sidebar:
    st.header("Global Filters")
    st.button("Reset filters", on_click=reset_global_filters, use_container_width=True)

    year_range = st.slider(
        "Year range",
        min_value=filter_options["year_min"],
        max_value=filter_options["year_max"],
        value=st.session_state.get("year_range", default_year_range),
        key="year_range",
    )
    tournament = st.selectbox(
        "Tournament",
        options=["All", *filter_options["tournaments"]],
        key="tournament_filter",
    )
    team_filter = st.selectbox(
        "Team",
        options=["All", *filter_options["teams"]],
        key="team_filter",
    )
    country = st.selectbox(
        "Host country",
        options=["All", *filter_options["countries"]],
        key="country_filter",
    )
    venue_mode = st.radio(
        "Venue type",
        options=["All matches", "Only neutral", "Only non-neutral"],
        key="venue_filter",
    )

filtered_df = apply_global_filters(
    matches_df=matches_df,
    year_range=year_range,
    tournament=tournament,
    team=team_filter,
    country=country,
    venue_mode=venue_mode,
)

st.sidebar.metric("Matches after filters", format_int(len(filtered_df.index)))

if filtered_df.empty:
    st.warning("No matches remain after applying the selected filters.")
    st.stop()

team_ranking_df = build_team_ranking(filtered_df)
outcome_distribution_df = build_outcome_distribution(filtered_df)
venue_comparison_df = build_venue_comparison(filtered_df)
yearly_trends_df = build_yearly_trends(filtered_df)

tabs = st.tabs(
    [
        "Overview",
        "Trends",
        "Teams",
        "Tournaments",
        "Home Advantage",
        "Match Explorer",
    ]
)

with tabs[0]:
    st.subheader("Overview")

    unique_teams = pd.unique(
        pd.concat([filtered_df["home_team"], filtered_df["away_team"]]).dropna()
    ).size
    avg_goals = filtered_df["total_goals"].mean()

    col1, col2, col3 = st.columns(3)
    col4, col5, col6 = st.columns(3)
    col1.metric("Matches", format_int(len(filtered_df.index)))
    col2.metric("Teams", format_int(unique_teams))
    col3.metric("Tournaments", format_int(filtered_df["tournament"].nunique()))
    col4.metric("Host countries", format_int(filtered_df["country"].nunique()))
    col5.metric(
        "Date range",
        f"{filtered_df['date'].min().date()} to {filtered_df['date'].max().date()}",
    )
    col6.metric("Average goals", format_float(avg_goals, 2))

    chart_col1, chart_col2 = st.columns(2)
    with chart_col1:
        matches_yearly_df = (
            filtered_df.groupby("year", as_index=False)
            .size()
            .rename(columns={"size": "matches"})
        )
        st.plotly_chart(
            matches_by_year_chart(matches_yearly_df),
            use_container_width=True,
        )
    with chart_col2:
        st.plotly_chart(
            outcome_distribution_chart(outcome_distribution_df),
            use_container_width=True,
        )

    st.markdown("#### Key takeaways")
    for insight in build_overview_insights(filtered_df)[:5]:
        st.markdown(f"- {insight}")

with tabs[1]:
    st.subheader("Trends")

    smoothing_mode = st.selectbox(
        "Smoothing",
        options=["No smoothing", "5-year rolling mean", "10-year rolling mean"],
        index=0,
    )
    smoothing_window = {"No smoothing": 1, "5-year rolling mean": 5, "10-year rolling mean": 10}[
        smoothing_mode
    ]
    trends_df = apply_smoothing(yearly_trends_df, smoothing_window)

    col1, col2 = st.columns(2)
    with col1:
        st.plotly_chart(
            metric_trend_chart(
                trends_df,
                metric="matches",
                title="Matches by Year",
                y_label="Matches",
            ),
            use_container_width=True,
        )
        st.plotly_chart(
            metric_trend_chart(
                trends_df,
                metric="draw_share",
                title="Draw Share by Year",
                y_label="Draw share, %",
            ),
            use_container_width=True,
        )
    with col2:
        st.plotly_chart(
            metric_trend_chart(
                trends_df,
                metric="avg_goals",
                title="Average Goals by Year",
                y_label="Goals per match",
            ),
            use_container_width=True,
        )
        non_neutral_df = trends_df.dropna(subset=["home_win_share"])
        if non_neutral_df.empty:
            show_empty_state("There are no non-neutral matches in the current filter.")
        else:
            st.plotly_chart(
                metric_trend_chart(
                    non_neutral_df,
                    metric="home_win_share",
                    title="Home Win Share by Year (Non-neutral Matches)",
                    y_label="Home win share, %",
                ),
                use_container_width=True,
            )

with tabs[2]:
    st.subheader("Teams")

    selected_team = st.selectbox(
        "Select team",
        options=team_ranking_df["team"].tolist(),
    )
    team_long_df = build_team_long(filtered_df)
    selected_team_df = team_long_df.loc[team_long_df["team"] == selected_team].copy()

    if selected_team_df.empty:
        show_empty_state("No matches are available for the selected team.")
    else:
        team_kpis = summarize_team(selected_team_df)
        kpi_cols = st.columns(5)
        kpi_cols[0].metric("Matches", format_int(team_kpis["matches"]))
        kpi_cols[1].metric("Wins", format_int(team_kpis["wins"]))
        kpi_cols[2].metric("Draws", format_int(team_kpis["draws"]))
        kpi_cols[3].metric("Losses", format_int(team_kpis["losses"]))
        kpi_cols[4].metric("Win rate", f"{format_float(float(team_kpis['win_rate']), 1)}%")

        kpi_cols2 = st.columns(4)
        kpi_cols2[0].metric("Goals for", format_int(team_kpis["goals_for"]))
        kpi_cols2[1].metric("Goals against", format_int(team_kpis["goals_against"]))
        kpi_cols2[2].metric("Goal difference", format_int(team_kpis["goal_difference"]))
        kpi_cols2[3].metric(
            "Average goals scored",
            format_float(float(team_kpis["avg_goals_for"]), 2),
        )

        yearly_df = yearly_team_results(selected_team_df)
        chart_col1, chart_col2 = st.columns(2)
        with chart_col1:
            st.plotly_chart(
                metric_trend_chart(
                    yearly_df,
                    metric="matches",
                    title=f"{selected_team}: Matches by Year",
                    y_label="Matches",
                ),
                use_container_width=True,
            )
        with chart_col2:
            st.plotly_chart(
                team_results_stacked_chart(yearly_df),
                use_container_width=True,
            )

        opponents_df = top_team_opponents(selected_team_df)
        st.plotly_chart(
            top_opponents_chart(opponents_df),
            use_container_width=True,
        )

        st.markdown("#### Latest 20 matches")
        latest_df = latest_team_matches(selected_team_df)
        latest_df["date"] = latest_df["date"].dt.date
        st.dataframe(latest_df, use_container_width=True, hide_index=True)

with tabs[3]:
    st.subheader("Tournaments")

    top_tournaments_df = (
        filtered_df.groupby("tournament", as_index=False)
        .size()
        .rename(columns={"size": "matches"})
        .sort_values(["matches", "tournament"], ascending=[False, True])
    )
    st.plotly_chart(
        top_tournaments_chart(top_tournaments_df),
        use_container_width=True,
    )

    selected_tournament = st.selectbox(
        "Select tournament",
        options=top_tournaments_df["tournament"].tolist(),
    )
    tournament_df = filtered_df.loc[filtered_df["tournament"] == selected_tournament].copy()

    if tournament_df.empty:
        show_empty_state("No matches are available for the selected tournament.")
    else:
        tournament_kpi_cols = st.columns(4)
        tournament_kpi_cols[0].metric("Matches", format_int(len(tournament_df.index)))
        tournament_kpi_cols[1].metric(
            "Teams",
            format_int(
                pd.unique(
                    pd.concat([tournament_df["home_team"], tournament_df["away_team"]]).dropna()
                ).size
            ),
        )
        tournament_kpi_cols[2].metric(
            "Average goals",
            format_float(tournament_df["total_goals"].mean(), 2),
        )
        tournament_kpi_cols[3].metric(
            "Date range",
            f"{tournament_df['date'].min().date()} to {tournament_df['date'].max().date()}",
        )

        chart_col1, chart_col2 = st.columns(2)
        with chart_col1:
            tournament_year_df = (
                tournament_df.groupby("year", as_index=False)
                .size()
                .rename(columns={"size": "matches"})
            )
            st.plotly_chart(
                tournament_yearly_chart(tournament_year_df),
                use_container_width=True,
            )
        with chart_col2:
            tournament_team_df = tournament_team_summary(tournament_df).head(10)
            st.plotly_chart(
                top_teams_chart(
                    tournament_team_df,
                    metric="wins",
                    title="Top Teams in Tournament by Wins",
                    x_label="Wins",
                    limit=10,
                ),
                use_container_width=True,
            )

        st.markdown("#### Biggest wins in this tournament")
        big_wins_df = biggest_wins(tournament_df, limit=10).copy()
        big_wins_df["date"] = big_wins_df["date"].dt.date
        st.dataframe(big_wins_df, use_container_width=True, hide_index=True)

with tabs[4]:
    st.subheader("Home Advantage")
    st.caption(
        "On neutral venues, the labels `home` and `away` describe record position in the "
        "dataset, not a real hosting advantage."
    )

    home_advantage_df = (
        filtered_df.assign(
            venue_type=filtered_df["neutral"].map({True: "Neutral", False: "Non-neutral"})
        )
        .assign(venue_type=lambda df: df["venue_type"].fillna("Unknown"))
        .groupby("venue_type", as_index=False)
        .agg(
            matches=("date", "size"),
            home_goals=("home_score", "mean"),
            away_goals=("away_score", "mean"),
        )
    )

    comparison_pivot = venue_comparison_df.pivot(
        index="venue_type", columns="result", values="share_pct"
    ).fillna(0.0)

    st.plotly_chart(
        venue_comparison_chart(venue_comparison_df),
        use_container_width=True,
    )

    merged_df = home_advantage_df.merge(
        comparison_pivot.reset_index(), on="venue_type", how="left"
    ).sort_values("venue_type")
    st.dataframe(
        merged_df.rename(
            columns={
                "venue_type": "Venue type",
                "matches": "Matches",
                "home_goals": "Average home goals",
                "away_goals": "Average away goals",
                "Home win": "Home win share, %",
                "Draw": "Draw share, %",
                "Away win": "Away win share, %",
            }
        ).round(2),
        use_container_width=True,
        hide_index=True,
    )

    non_neutral_home = comparison_pivot.loc["Non-neutral", "Home win"] if "Non-neutral" in comparison_pivot.index and "Home win" in comparison_pivot.columns else None
    neutral_home = comparison_pivot.loc["Neutral", "Home win"] if "Neutral" in comparison_pivot.index and "Home win" in comparison_pivot.columns else None
    if non_neutral_home is not None and neutral_home is not None:
        st.markdown(
            f"Home-win share changes from **{format_float(non_neutral_home, 1)}%** on non-neutral "
            f"fields to **{format_float(neutral_home, 1)}%** on neutral fields."
        )

with tabs[5]:
    st.subheader("Match Explorer")

    explorer_col1, explorer_col2, explorer_col3, explorer_col4 = st.columns(4)
    with explorer_col1:
        team_search = st.text_input("Team search", value="")
    with explorer_col2:
        min_total_goals = st.number_input(
            "Minimum total goals",
            min_value=0,
            max_value=50,
            value=0,
            step=1,
        )
    with explorer_col3:
        draws_only = st.checkbox("Only draws", value=False)
    with explorer_col4:
        big_wins_only = st.checkbox("Only big wins (goal difference >= 5)", value=False)

    explorer_df = apply_match_explorer_filters(
        matches_df=filtered_df,
        team_search=team_search,
        min_total_goals=int(min_total_goals),
        draws_only=draws_only,
        big_wins_only=big_wins_only,
    )

    if explorer_df.empty:
        show_empty_state("No matches satisfy the current explorer filters.")
    else:
        display_df = explorer_df[
            [
                "date",
                "home_team",
                "away_team",
                "home_score",
                "away_score",
                "tournament",
                "city",
                "country",
                "neutral",
            ]
        ].copy()
        display_df["date"] = display_df["date"].dt.date
        st.dataframe(display_df, use_container_width=True, hide_index=True)

        csv_buffer = StringIO()
        display_df.to_csv(csv_buffer, index=False)
        st.download_button(
            label="Download filtered matches as CSV",
            data=csv_buffer.getvalue(),
            file_name="filtered_matches.csv",
            mime="text/csv",
        )
