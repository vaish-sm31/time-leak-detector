from __future__ import annotations

from src.ingest import load_and_validate
from src.features import compute_ticket_metrics
from src.simulator import simulate_intervention_range


def main() -> None:
    tickets, history = load_and_validate()
    metrics = compute_ticket_metrics(tickets, history)

    out = simulate_intervention_range(
        metrics,
        hourly_cost=85.0,
        reduce_queue_pct=0.20,
        reduce_idle_pct=0.15,
        reduce_handoffs_pct=0.25,
    )

    print("Original Cost:", round(out["original_cost"], 2))
    print("\nSavings Range (Low/Base/High):")
    print("Low :", round(out["low"]["savings"], 2), "| multiplier:", out["low"]["handoff_idle_multiplier"])
    print("Base:", round(out["base"]["savings"], 2), "| multiplier:", out["base"]["handoff_idle_multiplier"])
    print("High:", round(out["high"]["savings"], 2), "| multiplier:", out["high"]["handoff_idle_multiplier"])


if __name__ == "__main__":
    main()