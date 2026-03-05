from __future__ import annotations

import pandas as pd


def add_cost_estimates(metrics: pd.DataFrame, hourly_cost: float = 85.0) -> pd.DataFrame:
    """
    Adds estimated cost of leakage.
    hourly_cost default = blended IT ops cost assumption.
    """
    m = metrics.copy()
    m["leak_hours"] = m["queue_hours"] + m["idle_hours"]
    m["estimated_leak_cost"] = m["leak_hours"] * hourly_cost
    return m