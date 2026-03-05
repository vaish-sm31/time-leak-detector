from __future__ import annotations

import json
import os

import streamlit as st

from src.fact_checker import strip_numbers_used, validate_numbers_used
from src.features import compute_ticket_metrics
from src.ingest import load_and_validate
from src.leakage_engine import rank_leakage, rank_status_leakage
from src.narrative_llm import build_exec_payload, generate_executive_summary
from src.simulator import simulate_intervention_range
from src.tenancy import scope_by_team
from src.timeline import build_ticket_timeline


st.set_page_config(page_title="Time Leak Detector (ITSM)", layout="wide")


@st.cache_data
def load_all():
    tickets, history = load_and_validate()
    metrics = compute_ticket_metrics(tickets, history)
    return tickets, history, metrics


def to_csv_bytes(df):
    return df.to_csv(index=False).encode("utf-8")


def main():
    st.title("Time Leak Detector (ITSM)")

    tickets, history, metrics = load_all()

    st.sidebar.header("Scope")
    teams = sorted(tickets["team_id"].unique().tolist())
    team_choice = st.sidebar.selectbox("Team scope", ["ALL"] + teams)

    if team_choice != "ALL":
        tickets_use, history_use = scope_by_team(tickets, history, team_id=team_choice)
        metrics_use = compute_ticket_metrics(tickets_use, history_use)
    else:
        tickets_use, history_use, metrics_use = tickets, history, metrics

    tabs = st.tabs(
        ["Overview", "Leakage Breakdown", "Simulator", "Executive Summary", "Ticket Timeline"]
    )

    # -------------------- Overview --------------------
    with tabs[0]:
        st.subheader("Dataset Snapshot")
        c1, c2, c3 = st.columns(3)
        c1.metric("Tickets", len(tickets_use))
        c2.metric("Status rows", len(history_use))
        c3.metric("Avg cycle hours", round(float(metrics_use["cycle_hours"].mean()), 2))

        st.write("Sample metrics (first 10 rows):")
        st.dataframe(
            metrics_use[
                ["ticket_id", "cycle_hours", "queue_hours", "idle_hours", "handoff_count"]
            ].head(10)
        )

        st.subheader("Exports")
        st.download_button(
            "Download metrics CSV",
            data=to_csv_bytes(metrics_use),
            file_name="metrics.csv",
            mime="text/csv",
        )
        st.download_button(
            "Download tickets CSV",
            data=to_csv_bytes(tickets_use),
            file_name="tickets.csv",
            mime="text/csv",
        )
        st.download_button(
            "Download status history CSV",
            data=to_csv_bytes(history_use),
            file_name="status_history.csv",
            mime="text/csv",
        )

    # -------------------- Leakage Breakdown --------------------
    with tabs[1]:
        st.subheader("Leakage Rankings")

        tables = rank_leakage(metrics_use)

        st.write("Leakage by Team")
        st.dataframe(tables["by_team"])
        st.download_button(
            "Download leakage by team CSV",
            data=to_csv_bytes(tables["by_team"]),
            file_name="leakage_by_team.csv",
            mime="text/csv",
        )

        st.write("Leakage by Category")
        st.dataframe(tables["by_category"])
        st.download_button(
            "Download leakage by category CSV",
            data=to_csv_bytes(tables["by_category"]),
            file_name="leakage_by_category.csv",
            mime="text/csv",
        )

        st.write("Leakage by Priority")
        st.dataframe(tables["by_priority"])
        st.download_button(
            "Download leakage by priority CSV",
            data=to_csv_bytes(tables["by_priority"]),
            file_name="leakage_by_priority.csv",
            mime="text/csv",
        )

        st.write("Worst Tickets")
        worst25 = tables["worst_tickets"].head(25)
        st.dataframe(worst25)
        st.download_button(
            "Download worst tickets CSV",
            data=to_csv_bytes(worst25),
            file_name="worst_tickets_top25.csv",
            mime="text/csv",
        )

        st.subheader("Workflow Bottlenecks (Time Spent by Status)")
        by_status = rank_status_leakage(history_use)
        st.dataframe(by_status)
        st.download_button(
            "Download time spent by status CSV",
            data=to_csv_bytes(by_status),
            file_name="time_spent_by_status.csv",
            mime="text/csv",
        )

    # -------------------- Simulator (Step 9) --------------------
    with tabs[2]:
        st.subheader("Intervention Simulator (Savings Range)")

        hourly_cost = st.slider("Hourly cost ($/hr)", 20, 300, 85)
        reduce_queue_pct = st.slider("Reduce queue time (%)", 0, 60, 20) / 100.0
        reduce_idle_pct = st.slider("Reduce idle time (%)", 0, 60, 15) / 100.0
        reduce_handoffs_pct = st.slider("Reduce handoffs (%)", 0, 60, 25) / 100.0

        sim = simulate_intervention_range(
            metrics_use,
            hourly_cost=float(hourly_cost),
            reduce_queue_pct=float(reduce_queue_pct),
            reduce_idle_pct=float(reduce_idle_pct),
            reduce_handoffs_pct=float(reduce_handoffs_pct),
        )

        st.metric("Original Cost", f"${sim['original_cost']:,.2f}")

        st.write("Savings (Low/Base/High):")
        st.write(
            {
                "low": round(float(sim["low"]["savings"]), 2),
                "base": round(float(sim["base"]["savings"]), 2),
                "high": round(float(sim["high"]["savings"]), 2),
            }
        )

        st.write("Assumptions used:")
        st.write(
            {
                "hourly_cost": float(hourly_cost),
                "reduce_queue_pct": float(reduce_queue_pct),
                "reduce_idle_pct": float(reduce_idle_pct),
                "reduce_handoffs_pct": float(reduce_handoffs_pct),
            }
        )

        sim_export = {
            "original_cost": float(sim["original_cost"]),
            "assumptions": {
                "hourly_cost": float(hourly_cost),
                "reduce_queue_pct": float(reduce_queue_pct),
                "reduce_idle_pct": float(reduce_idle_pct),
                "reduce_handoffs_pct": float(reduce_handoffs_pct),
            },
            "range": {
                "low": {"savings": float(sim["low"]["savings"])},
                "base": {"savings": float(sim["base"]["savings"])},
                "high": {"savings": float(sim["high"]["savings"])},
            },
        }

        st.download_button(
            "Download simulator output JSON",
            data=json.dumps(sim_export, indent=2).encode("utf-8"),
            file_name="simulator_output.json",
            mime="application/json",
        )

    # -------------------- Executive Summary --------------------
    with tabs[3]:
        st.subheader("Executive Narrative (LLM + Fact-Checked)")

        if not os.environ.get("OPENAI_API_KEY"):
            st.warning(
                "OPENAI_API_KEY is not set. Export it in your terminal before running Streamlit."
            )
            st.stop()

        tables = rank_leakage(metrics_use)
        status_tbl = rank_status_leakage(history_use)
        sim = simulate_intervention_range(metrics_use)

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

        if st.button("Generate Executive Summary", key="btn_exec_summary"):
            out = generate_executive_summary(payload)
            ok, errors = validate_numbers_used(out, payload)

            if not ok:
                st.error(
                    "Narrative failed fact-check. Returning safe output without numbers_used."
                )
                for e in errors:
                    st.write("-", e)
                out = strip_numbers_used(out)
            else:
                st.success("Narrative passed fact-check.")

            st.json(out)

            st.download_button(
                "Download narrative JSON",
                data=json.dumps(out, indent=2).encode("utf-8"),
                file_name="executive_summary.json",
                mime="application/json",
            )

    # -------------------- Ticket Timeline (Step 8 drill-down) --------------------
    with tabs[4]:
        st.subheader("Ticket Timeline (Drill-Down Evidence)")

        ticket_id = st.selectbox(
            "Select a ticket_id",
            options=metrics_use["ticket_id"].tolist(),
            key="ticket_timeline_select",
        )

        tl = build_ticket_timeline(ticket_id, history_use)

        if tl.empty:
            st.warning("No timeline data found for this ticket.")
        else:
            c1, c2, c3 = st.columns(3)
            c1.metric("Statuses", len(tl))
            c2.metric("Total status hours", round(float(tl["duration_hours"].sum()), 2))
            c3.metric("Total gap hours", round(float(tl["gap_hours"].sum()), 2))

            st.write("Lifecycle timeline (ordered):")
            st.dataframe(tl)

            st.download_button(
                "Download ticket timeline CSV",
                data=to_csv_bytes(tl),
                file_name=f"timeline_{ticket_id}.csv",
                mime="text/csv",
            )

            st.write("Largest duration statuses (top 5):")
            top5 = tl.sort_values("duration_hours", ascending=False).head(5)[
                ["status", "assigned_team", "duration_hours"]
            ]
            st.dataframe(top5)


if __name__ == "__main__":
    main()