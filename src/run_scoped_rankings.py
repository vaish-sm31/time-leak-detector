from __future__ import annotations

from src.ingest import load_and_validate
from src.features import compute_ticket_metrics
from src.leakage_engine import rank_leakage, rank_status_leakage
from src.tenancy import scope_by_team


def main() -> None:
    tickets, history = load_and_validate()

    team_id = "TIER1"  # change later
    t_scoped, h_scoped = scope_by_team(tickets, history, team_id=team_id)

    metrics = compute_ticket_metrics(t_scoped, h_scoped)
    tables = rank_leakage(metrics)

    print(f"\n=== Scoped Rankings for {team_id} ===")
    print("\nBy Priority:")
    print(tables["by_priority"])

    print("\nTime Spent by Status (Top):")
    print(rank_status_leakage(h_scoped).head(8))


if __name__ == "__main__":
    main()