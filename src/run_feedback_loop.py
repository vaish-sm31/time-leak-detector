from __future__ import annotations

from src.ingest import load_and_validate
from src.features import compute_ticket_metrics
from src.simulator import simulate_intervention_range
from src.feedback_loop import (
    apply_actual_improvement_with_noise,
    evaluate_prediction_vs_actual,
    calibration_error,
)


def main() -> None:
    tickets, history = load_and_validate()
    metrics = compute_ticket_metrics(tickets, history)

    # predicted (base)
    pred = simulate_intervention_range(
        metrics,
        hourly_cost=85.0,
        reduce_queue_pct=0.20,
        reduce_idle_pct=0.15,
        reduce_handoffs_pct=0.25,
    )
    predicted_savings = pred["base"]["savings"]

    # synthetic "actual"
    after = apply_actual_improvement_with_noise(
        metrics,
        reduce_queue_pct=0.20,
        reduce_idle_pct=0.15,
        reduce_handoffs_pct=0.25,
        noise_std=0.05,
        seed=7,
    )

    observed = evaluate_prediction_vs_actual(metrics, after, hourly_cost=85.0)

    cal = calibration_error(predicted_savings, observed["observed_savings"])

    print("Predicted savings (base):", round(cal["predicted_savings"], 2))
    print("Observed savings:", round(cal["observed_savings"], 2))
    print("Absolute error:", round(cal["absolute_error"], 2))
    print("Percent error:", round(cal["percent_error"] * 100, 2), "%")


if __name__ == "__main__":
    main()