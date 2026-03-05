from __future__ import annotations

from src.ingest import load_and_validate
from src.features import compute_ticket_metrics
from src.cost_model import add_cost_estimates


def main():
    tickets, history = load_and_validate()
    metrics = compute_ticket_metrics(tickets, history)
    metrics = add_cost_estimates(metrics)

    print("Total Estimated Leakage Cost:")
    print(metrics["estimated_leak_cost"].sum())

    print("\nTop 10 Most Expensive Tickets:")
    print(
        metrics.sort_values("estimated_leak_cost", ascending=False)[
            ["ticket_id", "team_id", "priority", "estimated_leak_cost"]
        ].head(10)
    )


if __name__ == "__main__":
    main()