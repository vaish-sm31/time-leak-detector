from __future__ import annotations

from typing import Tuple

import pandas as pd

# Optional: if pandera exists use it.
# If not installed, manual validation.
try:
    import pandera as pa
    from pandera import Column, Check, DataFrameSchema
except Exception:  # pragma: no cover
    pa = None
    Column = Check = DataFrameSchema = None


REQUIRED_TICKETS_COLS = [
    "ticket_id",
    "created_at",
    "resolved_at",
    "priority",
    "team_id",
    "category",
]

REQUIRED_HISTORY_COLS = [
    "ticket_id",
    "status",
    "status_start",
    "status_end",
    "assigned_team",
]

ALLOWED_PRIORITIES = {"P0", "P1", "P2", "P3"}


def _ensure_datetime_utc(df: pd.DataFrame, col: str) -> None:
    """
    Convert df[col] to timezone-aware UTC datetimes (in-place).
    """
    if col not in df.columns:
        return
    df[col] = pd.to_datetime(df[col], errors="coerce", utc=True, format="ISO8601")


def _require_columns(df: pd.DataFrame, required: list[str], name: str) -> None:
    missing = [c for c in required if c not in df.columns]
    if missing:
        raise ValueError(f"{name} is missing required columns: {missing}")


def _manual_validate(tickets: pd.DataFrame, history: pd.DataFrame) -> Tuple[pd.DataFrame, pd.DataFrame]:
    t = tickets.copy()
    h = history.copy()

    _require_columns(t, REQUIRED_TICKETS_COLS, "tickets")
    _require_columns(h, REQUIRED_HISTORY_COLS, "status_history")

    # Coerce datetimes
    for c in ["created_at", "resolved_at"]:
        _ensure_datetime_utc(t, c)
    for c in ["status_start", "status_end"]:
        _ensure_datetime_utc(h, c)

    # Null checks
    if t["ticket_id"].isna().any():
        raise ValueError("tickets.ticket_id has nulls")
    if h["ticket_id"].isna().any():
        raise ValueError("status_history.ticket_id has nulls")

    # Timestamp parse checks
    if t["created_at"].isna().any():
        raise ValueError("tickets.created_at has unparseable timestamps (NaT)")
    if t["resolved_at"].isna().any():
        raise ValueError("tickets.resolved_at has unparseable timestamps (NaT)")
    if h["status_start"].isna().any():
        raise ValueError("status_history.status_start has unparseable timestamps (NaT)")
    if h["status_end"].isna().any():
        raise ValueError("status_history.status_end has unparseable timestamps (NaT)")

    # Ordering checks
    bad_ticket_order = (t["resolved_at"] < t["created_at"]).sum()
    if bad_ticket_order:
        raise ValueError(f"{bad_ticket_order} tickets have resolved_at < created_at")

    bad_status_order = (h["status_end"] < h["status_start"]).sum()
    if bad_status_order:
        raise ValueError(f"{bad_status_order} status rows have status_end < status_start")

    # Allowed priorities
    bad_pri = (~t["priority"].isin(ALLOWED_PRIORITIES)).sum()
    if bad_pri:
        bad_vals = sorted(t.loc[~t["priority"].isin(ALLOWED_PRIORITIES), "priority"].dropna().unique().tolist())
        raise ValueError(f"{bad_pri} tickets have invalid priority values: {bad_vals}")

    # Basic string non-empty
    if (t["team_id"].astype(str).str.strip() == "").any():
        raise ValueError("tickets.team_id has empty strings")
    if (t["category"].astype(str).str.strip() == "").any():
        raise ValueError("tickets.category has empty strings")
    if (h["status"].astype(str).str.strip() == "").any():
        raise ValueError("status_history.status has empty strings")
    if (h["assigned_team"].astype(str).str.strip() == "").any():
        raise ValueError("status_history.assigned_team has empty strings")

    return t, h


def _pandera_validate(tickets: pd.DataFrame, history: pd.DataFrame) -> Tuple[pd.DataFrame, pd.DataFrame]:
    # Coerce datetimes first so pandera can check types reliably
    t = tickets.copy()
    h = history.copy()

    _require_columns(t, REQUIRED_TICKETS_COLS, "tickets")
    _require_columns(h, REQUIRED_HISTORY_COLS, "status_history")

    for c in ["created_at", "resolved_at"]:
        _ensure_datetime_utc(t, c)
    for c in ["status_start", "status_end"]:
        _ensure_datetime_utc(h, c)

    tickets_schema = DataFrameSchema(
        {
            "ticket_id": Column(str, nullable=False),
            "created_at": Column("datetime64[ns, UTC]", nullable=False),
            "resolved_at": Column("datetime64[ns, UTC]", nullable=False),
            "priority": Column(str, Check.isin(ALLOWED_PRIORITIES), nullable=False),
            "team_id": Column(str, nullable=False),
            "category": Column(str, nullable=False),
        },
        strict=False,
        coerce=False,
    )

    history_schema = DataFrameSchema(
        {
            "ticket_id": Column(str, nullable=False),
            "status": Column(str, nullable=False),
            "status_start": Column("datetime64[ns, UTC]", nullable=False),
            "status_end": Column("datetime64[ns, UTC]", nullable=False),
            "assigned_team": Column(str, nullable=False),
        },
        strict=False,
        coerce=False,
    )

    t = tickets_schema.validate(t)
    h = history_schema.validate(h)

    # Ordering checks
    if (t["resolved_at"] < t["created_at"]).any():
        raise ValueError("Found tickets where resolved_at < created_at")

    if (h["status_end"] < h["status_start"]).any():
        raise ValueError("Found status rows where status_end < status_start")

    return t, h


def validate_inputs(tickets: pd.DataFrame, history: pd.DataFrame) -> Tuple[pd.DataFrame, pd.DataFrame]:
    """
    Validate tickets + status_history against the data contract.

    Returns validated (tickets_df, history_df) with timestamps coerced to UTC datetimes.
    Raises ValueError on any contract violation.
    """
    if pa is not None:
        return _pandera_validate(tickets, history)
    return _manual_validate(tickets, history)