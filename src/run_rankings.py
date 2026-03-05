from __future__ import annotations

from src.ingest import load_and_validate
from src.features import compute_ticket_metrics
from src.leakage_engine import rank_leakage, rank_status_leakage


def main() -> None:
    tickets, history = load_and_validate()
    metrics = compute_ticket_metrics(tickets, history)
    tables = rank_leakage(metrics)

    print("\n=== Leakage by Team (Top) ===")
    print(tables["by_team"].head(10))

    print("\n=== Leakage by Category (Top) ===")
    print(tables["by_category"].head(10))

    print("\n=== Leakage by Priority ===")
    print(tables["by_priority"])

    print("\n=== Worst Tickets (Top 10) ===")
    print(tables["worst_tickets"].head(10))

    # NEW: Status-level workflow bottlenecks
    print("\n=== Time Spent by Status (Top) ===")
    by_status = rank_status_leakage(history)
    print(by_status.head(10))


if __name__ == "__main__":
    main()