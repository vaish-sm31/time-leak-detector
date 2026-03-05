from __future__ import annotations

from src.ingest import load_and_validate
from src.features import compute_ticket_metrics
from src.simulator import simulate_intervention_range


def main():
    tickets, history = load_and_validate()
    metrics = compute_ticket_metrics(tickets, history)

    sim = simulate_intervention_range(metrics)

    print("\n=== Intervention Simulator ===")

    print(f"Original Cost: ${sim['original_cost']:,.2f}")

    print("\nSavings Range:")
    print(f"Low : ${sim['low']['savings']:,.2f}")
    print(f"Base: ${sim['base']['savings']:,.2f}")
    print(f"High: ${sim['high']['savings']:,.2f}")


if __name__ == "__main__":
    main()