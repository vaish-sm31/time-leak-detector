from __future__ import annotations

import pandas as pd


def _scenario_apply(
    m: pd.DataFrame,
    reduce_queue_pct: float,
    reduce_idle_pct: float,
    reduce_handoffs_pct: float,
    handoff_idle_multiplier: float,
) -> pd.DataFrame:
    """
    Applies reductions to queue + idle, and models handoff reduction as additional idle reduction.
    handoff_idle_multiplier = how many idle hours are typically caused per handoff (assumption).
    """
    x = m.copy()

    # baseline
    x["leak_hours"] = x["queue_hours"] + x["idle_hours"]

    # reduce queue directly
    x["new_queue_hours"] = x["queue_hours"] * (1 - reduce_queue_pct)

    # reduce idle directly
    x["new_idle_hours"] = x["idle_hours"] * (1 - reduce_idle_pct)

    # model handoff reduction → extra idle saved
    # (handoffs avoided) * (idle hours per handoff) but capped so idle never goes negative
    avoided_handoffs = x["handoff_count"] * reduce_handoffs_pct
    extra_idle_saved = avoided_handoffs * handoff_idle_multiplier

    x["new_idle_hours"] = (x["new_idle_hours"] - extra_idle_saved).clip(lower=0.0)

    x["new_leak_hours"] = x["new_queue_hours"] + x["new_idle_hours"]
    return x


def simulate_intervention_range(
    metrics: pd.DataFrame,
    hourly_cost: float = 85.0,
    reduce_queue_pct: float = 0.20,
    reduce_idle_pct: float = 0.15,
    reduce_handoffs_pct: float = 0.25,
    handoff_idle_multiplier_low: float = 0.25,
    handoff_idle_multiplier_base: float = 0.50,
    handoff_idle_multiplier_high: float = 0.75,
) -> dict:
    """
    Returns low/base/high savings using different handoff impact assumptions.
    Percent inputs are decimals (0.2 = 20%).
    """

    m = metrics.copy()

    original_cost = ((m["queue_hours"] + m["idle_hours"]).sum()) * hourly_cost

    def compute(mult: float) -> dict:
        x = _scenario_apply(
            m,
            reduce_queue_pct=reduce_queue_pct,
            reduce_idle_pct=reduce_idle_pct,
            reduce_handoffs_pct=reduce_handoffs_pct,
            handoff_idle_multiplier=mult,
        )
        new_cost = x["new_leak_hours"].sum() * hourly_cost
        return {
            "handoff_idle_multiplier": mult,
            "new_cost": new_cost,
            "savings": original_cost - new_cost,
        }

    low = compute(handoff_idle_multiplier_low)
    base = compute(handoff_idle_multiplier_base)
    high = compute(handoff_idle_multiplier_high)

    return {
        "original_cost": original_cost,
        "low": low,
        "base": base,
        "high": high,
        "assumptions": {
            "hourly_cost": hourly_cost,
            "reduce_queue_pct": reduce_queue_pct,
            "reduce_idle_pct": reduce_idle_pct,
            "reduce_handoffs_pct": reduce_handoffs_pct,
        },
    }