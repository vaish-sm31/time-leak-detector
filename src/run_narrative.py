from __future__ import annotations

from src.fact_checker import validate_numbers_used, strip_numbers_used
from src.ingest import load_and_validate
from src.features import compute_ticket_metrics
from src.leakage_engine import rank_leakage, rank_status_leakage
from src.simulator import simulate_intervention_range
from src.narrative_llm import build_exec_payload, generate_executive_summary


def main() -> None:
    tickets, history = load_and_validate()
    metrics = compute_ticket_metrics(tickets, history)

    tables = rank_leakage(metrics)
    status_tbl = rank_status_leakage(history)

    sim = simulate_intervention_range(metrics)

    payload = build_exec_payload(
        team_table=tables["by_team"],
        category_table=tables["by_category"],
        priority_table=tables["by_priority"],
        status_table=status_tbl,
        original_cost=sim["original_cost"],
        savings_low=sim["low"]["savings"],
        savings_base=sim["base"]["savings"],
        savings_high=sim["high"]["savings"],
    )

    
    out = generate_executive_summary(payload)

    ok, errors = validate_numbers_used(out, payload)
    if not ok:
        print("❌ Narrative failed fact-check:")
        for e in errors:
            print(" -", e)
        out = strip_numbers_used(out)
        print("\n⚠️ Returning narrative with numbers_used removed.")
    else:
        print("✅ Narrative passed fact-check.")

    print(out)

if __name__ == "__main__":
    main()