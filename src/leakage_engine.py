from __future__ import annotations

import pandas as pd


def rank_leakage(metrics: pd.DataFrame) -> dict[str, pd.DataFrame]:
    """
    Returns ranked leakage tables for key dimensions.
    Expects columns: team_id, category, priority, cycle_hours, queue_hours, idle_hours.
    """
    m = metrics.copy()

    # Total leak = queue + idle (you can expand later)
    m["leak_hours"] = m["queue_hours"] + m["idle_hours"]

    by_team = (
        m.groupby("team_id", as_index=False)
        .agg(
            tickets=("ticket_id", "count"),
            total_leak_hours=("leak_hours", "sum"),
            avg_leak_hours=("leak_hours", "mean"),
            avg_cycle_hours=("cycle_hours", "mean"),
        )
        .sort_values("total_leak_hours", ascending=False)
        .reset_index(drop=True)
    )

    by_category = (
        m.groupby("category", as_index=False)
        .agg(
            tickets=("ticket_id", "count"),
            total_leak_hours=("leak_hours", "sum"),
            avg_leak_hours=("leak_hours", "mean"),
        )
        .sort_values("total_leak_hours", ascending=False)
        .reset_index(drop=True)
    )

    by_priority = (
        m.groupby("priority", as_index=False)
        .agg(
            tickets=("ticket_id", "count"),
            total_leak_hours=("leak_hours", "sum"),
            avg_leak_hours=("leak_hours", "mean"),
        )
        .sort_values("total_leak_hours", ascending=False)
        .reset_index(drop=True)
    )

    worst_tickets = (
        m[
            [
                "ticket_id",
                "team_id",
                "priority",
                "category",
                "cycle_hours",
                "queue_hours",
                "idle_hours",
                "leak_hours",
            ]
        ]
        .sort_values("leak_hours", ascending=False)
        .head(25)
        .reset_index(drop=True)
    )

    return {
        "by_team": by_team,
        "by_category": by_category,
        "by_priority": by_priority,
        "worst_tickets": worst_tickets,
    }


def rank_status_leakage(history: pd.DataFrame) -> pd.DataFrame:
    """
    Ranks total hours spent in each status across all tickets (workflow bottlenecks).
    Expects history columns: ticket_id, status, status_start, status_end
    """
    h = history.copy()
    h["duration_hours"] = (h["status_end"] - h["status_start"]).dt.total_seconds() / 3600.0

    by_status = (
        h.groupby("status", as_index=False)
        .agg(
            rows=("ticket_id", "count"),
            total_hours=("duration_hours", "sum"),
            avg_hours_per_row=("duration_hours", "mean"),
        )
        .sort_values("total_hours", ascending=False)
        .reset_index(drop=True)
    )

    total = by_status["total_hours"].sum()
    by_status["share_of_total_time"] = (by_status["total_hours"] / total).round(4)

    return by_status