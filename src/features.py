from __future__ import annotations

import pandas as pd

WAIT_STATUSES = {"WAITING_ON_CUSTOMER", "WAITING_ON_VENDOR", "BLOCKED"}


def compute_ticket_metrics(tickets: pd.DataFrame, history: pd.DataFrame) -> pd.DataFrame:
    """
    Produces a per-ticket metrics table used by the leakage engine + simulator.

    Requires:
      tickets columns: ticket_id, created_at, resolved_at, priority, team_id, category
      history columns: ticket_id, status, status_start, status_end, assigned_team
    """
    t = tickets.copy()
    h = history.copy()

    # --- Base durations per status row ---
    h["duration_hours"] = (h["status_end"] - h["status_start"]).dt.total_seconds() / 3600.0

    # --- Cycle time (ticket-level) ---
    t["cycle_hours"] = (t["resolved_at"] - t["created_at"]).dt.total_seconds() / 3600.0

    # --- Queue time: created -> first IN_PROGRESS ---
    first_in_progress = (
        h.loc[h["status"] == "IN_PROGRESS"]
        .sort_values(["ticket_id", "status_start"])
        .groupby("ticket_id", as_index=False)
        .first()[["ticket_id", "status_start"]]
        .rename(columns={"status_start": "first_touch_at"})
    )

    t = t.merge(first_in_progress, on="ticket_id", how="left")
    t["queue_hours"] = (t["first_touch_at"] - t["created_at"]).dt.total_seconds() / 3600.0
    t["queue_hours"] = t["queue_hours"].fillna(0).clip(lower=0)

    # --- Idle time: time spent in waiting states ---
    idle = (
        h.loc[h["status"].isin(WAIT_STATUSES)]
        .groupby("ticket_id", as_index=False)["duration_hours"]
        .sum()
        .rename(columns={"duration_hours": "idle_hours"})
    )
    t = t.merge(idle, on="ticket_id", how="left")
    t["idle_hours"] = t["idle_hours"].fillna(0.0)

    # --- Time-in-status: one column per status (evidence + explainability) ---
    per_status = (
        h.groupby(["ticket_id", "status"], as_index=False)["duration_hours"]
        .sum()
    )

    status_pivot = (
        per_status.pivot(index="ticket_id", columns="status", values="duration_hours")
        .fillna(0.0)
        .reset_index()
    )

    # flatten column names like time_in_NEW_hours, time_in_TRIAGE_hours, ...
    status_cols = [c for c in status_pivot.columns if c != "ticket_id"]
    status_pivot = status_pivot.rename(columns={c: f"time_in_{c}_hours" for c in status_cols})

    t = t.merge(status_pivot, on="ticket_id", how="left")
    # fill any missing status columns for tickets that never hit a status
    time_cols = [c for c in t.columns if c.startswith("time_in_") and c.endswith("_hours")]
    t[time_cols] = t[time_cols].fillna(0.0)

    # --- Handoff count: number of times assigned_team changes across lifecycle ---
    h_sorted = h.sort_values(["ticket_id", "status_start"]).copy()
    h_sorted["prev_team"] = h_sorted.groupby("ticket_id")["assigned_team"].shift(1)

    # first row per ticket has prev_team = NaN; we don't count that as a handoff
    h_sorted["handoff_event"] = (
        (h_sorted["prev_team"].notna()) & (h_sorted["assigned_team"] != h_sorted["prev_team"])
    ).astype(int)

    handoffs = (
        h_sorted.groupby("ticket_id", as_index=False)["handoff_event"]
        .sum()
        .rename(columns={"handoff_event": "handoff_count"})
    )

    t = t.merge(handoffs, on="ticket_id", how="left")
    t["handoff_count"] = t["handoff_count"].fillna(0).astype(int)

    return t