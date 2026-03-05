import numpy as np

from src.ingest import load_and_validate
from src.features import compute_ticket_metrics


def test_cycle_queue_idle_non_negative():
    tickets, history = load_and_validate()
    metrics = compute_ticket_metrics(tickets, history)

    assert (metrics["cycle_hours"] >= 0).all()
    assert (metrics["queue_hours"] >= 0).all()
    assert (metrics["idle_hours"] >= 0).all()


def test_queue_not_greater_than_cycle():
    tickets, history = load_and_validate()
    metrics = compute_ticket_metrics(tickets, history)

    # allow tiny floating tolerance
    assert (metrics["queue_hours"] <= metrics["cycle_hours"] + 1e-6).all()


def test_time_in_status_sums_close_to_cycle():
    """
    Your synthetic generator builds status rows that should approximately cover the lifecycle.
    We check that sum(time_in_*_hours) ~= cycle_hours (within tolerance) for most tickets.
    """
    tickets, history = load_and_validate()
    metrics = compute_ticket_metrics(tickets, history)

    time_cols = [c for c in metrics.columns if c.startswith("time_in_") and c.endswith("_hours")]
    assert len(time_cols) > 0

    sums = metrics[time_cols].sum(axis=1)
    diff = (metrics["cycle_hours"] - sums).abs()

   
    # Require 95% of tickets to be within 0.25 hours.
    within = (diff <= 0.25).mean()
    assert within >= 0.95, f"Only {within:.2%} tickets within tolerance"