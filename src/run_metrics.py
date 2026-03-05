from __future__ import annotations

from src.ingest import load_and_validate
from src.features import compute_ticket_metrics


def main() -> None:
    tickets, history = load_and_validate()
    metrics = compute_ticket_metrics(tickets, history)

    print(metrics[["ticket_id", "cycle_hours", "queue_hours", "idle_hours"]].head(10))
    print("\nSummary:")
    print(metrics[["cycle_hours", "queue_hours", "idle_hours"]].describe())


if __name__ == "__main__":
    main()