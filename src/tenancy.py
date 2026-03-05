from __future__ import annotations

import pandas as pd


def scope_by_team(
    tickets: pd.DataFrame,
    history: pd.DataFrame,
    team_id: str,
) -> tuple[pd.DataFrame, pd.DataFrame]:
    """
    Returns tickets + history scoped to a single team.

    Rule:
      - tickets are scoped by tickets.team_id
      - history is scoped by ticket_id belonging to that team (prevents cross-team bleed)
    """
    t = tickets.loc[tickets["team_id"] == team_id].copy()
    allowed = set(t["ticket_id"].unique())
    h = history.loc[history["ticket_id"].isin(allowed)].copy()
    return t, h