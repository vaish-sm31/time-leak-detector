from __future__ import annotations

import numpy as np
import pandas as pd


def apply_actual_improvement_with_noise(
    metrics: pd.DataFrame,
    reduce_queue_pct: float,
    reduce_idle_pct: float,
    reduce_handoffs_pct: float,
    noise_std: float = 0.05,
    seed: int = 7,
) -> pd.DataFrame:
    """
    Creates a synthetic 'observed' post-intervention outcome by applying reductions
    + small Gaussian noise (because real life never hits the plan perfectly).

    Output columns added:
      - queue_hours_after
      - idle_hours_after
    """
    rng = np.random.default_rng(seed)
    m = metrics.copy()

    # apply reductions
    m["queue_hours_after"] = m["queue_hours"] * (1 - float(reduce_queue_pct))
    m["idle_hours_after"] = m["idle_hours"] * (1 - float(reduce_idle_pct))

    # model handoff reduction as idle reduction (simple + explainable)
    avoided = m["handoff_count"] * float(reduce_handoffs_pct)

    # assume idle per avoided handoff ~0.5 hours (same as base assumption)
    m["idle_hours_after"] = (m["idle_hours_after"] - avoided * 0.5).clip(lower=0.0)

    # add noise (multiplicative)
    noise_q = rng.normal(0.0, float(noise_std), size=len(m))
    noise_i = rng.normal(0.0, float(noise_std), size=len(m))

    m["queue_hours_after"] = (m["queue_hours_after"] * (1 + noise_q)).clip(lower=0.0)
    m["idle_hours_after"] = (m["idle_hours_after"] * (1 + noise_i)).clip(lower=0.0)

    return m


def evaluate_prediction_vs_actual(
    metrics_before: pd.DataFrame,
    metrics_after: pd.DataFrame,
    hourly_cost: float = 85.0,
) -> dict:
    """
    Compares pre vs post (observed) improvement and returns costs + observed savings.
    """
    hourly_cost = float(hourly_cost)

    before_cost = float(((metrics_before["queue_hours"] + metrics_before["idle_hours"]).sum()) * hourly_cost)
    after_cost = float(((metrics_after["queue_hours_after"] + metrics_after["idle_hours_after"]).sum()) * hourly_cost)

    observed_savings = float(before_cost - after_cost)

    return {
        "before_cost": before_cost,
        "after_cost": after_cost,
        "observed_savings": observed_savings,
    }


def calibration_error(predicted_savings: float, observed_savings: float) -> dict:
    """
    Simple calibration: absolute error and percent error.

    percent_error is computed relative to |observed_savings| to avoid sign confusion.
    """
    predicted_savings = float(predicted_savings)
    observed_savings = float(observed_savings)

    abs_err = float(predicted_savings - observed_savings)

    denom = abs(observed_savings)
    pct_err = float(abs_err / denom) if denom > 1e-9 else float("nan")

    return {
        "predicted_savings": predicted_savings,
        "observed_savings": observed_savings,
        "absolute_error": abs_err,
        "percent_error": pct_err,
    }