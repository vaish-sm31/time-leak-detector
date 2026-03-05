from __future__ import annotations

import pandas as pd


def build_ticket_timeline(ticket_id: str, history: pd.DataFrame) -> pd.DataFrame:
    """
    Returns ordered timeline for a single ticket.
    Includes:
      - duration per status
      - gap between statuses
      - assigned team
    """

    h = history[history["ticket_id"] == ticket_id].copy()

    if h.empty:
        return pd.DataFrame()

    # ensure timestamps are datetime
    h["status_start"] = pd.to_datetime(h["status_start"], utc=True, errors="coerce")
    h["status_end"] = pd.to_datetime(h["status_end"], utc=True, errors="coerce")

    h = h.sort_values("status_start")

    # duration inside each status
    h["duration_hours"] = (
        (h["status_end"] - h["status_start"]).dt.total_seconds() / 3600.0
    )

    # gap between previous status end and next status start
    h["prev_end"] = h["status_end"].shift(1)
    h["gap_hours"] = (
        (h["status_start"] - h["prev_end"]).dt.total_seconds() / 3600.0
    )
    h["gap_hours"] = h["gap_hours"].fillna(0).clip(lower=0)

    # round for readability
    h["duration_hours"] = h["duration_hours"].round(3)
    h["gap_hours"] = h["gap_hours"].round(3)

    return h[
        [
            "ticket_id",
            "assigned_team",
            "status",
            "status_start",
            "status_end",
            "duration_hours",
            "gap_hours",
        ]
    ].reset_index(drop=True)