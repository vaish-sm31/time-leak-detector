from __future__ import annotations

from datetime import datetime, timedelta
import random
import uuid

import numpy as np
import pandas as pd


WAIT_STATUSES = {"WAITING_ON_CUSTOMER", "WAITING_ON_VENDOR", "BLOCKED"}


def _rand_dt(start: datetime, end: datetime) -> datetime:
    delta = end - start
    seconds = random.randint(0, int(delta.total_seconds()))
    return start + timedelta(seconds=seconds)


def generate_synthetic(n_tickets: int = 2000, seed: int = 42) -> tuple[pd.DataFrame, pd.DataFrame]:
    random.seed(seed)
    np.random.seed(seed)

    teams = ["TIER1", "TIER2", "PLATFORM", "NETWORK"]
    categories = ["Access", "Onboarding", "Outage", "Bug", "Request", "Billing"]
    priorities = ["P0", "P1", "P2", "P3"]

    start = datetime(2025, 10, 1)
    end = datetime(2026, 2, 1)

    tickets_rows = []
    history_rows = []

    for _ in range(n_tickets):
        ticket_id = f"TCKT-{uuid.uuid4().hex[:8].upper()}"
        created_at = _rand_dt(start, end)

        priority = random.choices(priorities, weights=[0.05, 0.15, 0.35, 0.45])[0]
        initial_team = random.choices(teams, weights=[0.45, 0.30, 0.15, 0.10])[0]
        category = random.choice(categories)

        # Base resolution time by priority
        base_hours = {"P0": 8, "P1": 24, "P2": 72, "P3": 120}[priority]

        # Lognormal noise makes it feel realistic (a few tickets become outliers)
        noise = max(1, int(np.random.lognormal(mean=3.0, sigma=0.4)))
        total_hours = int(base_hours * (0.6 + 0.01 * noise))

        resolved_at = created_at + timedelta(hours=total_hours)

        # Lifecycle steps
        steps = ["NEW", "TRIAGE", "IN_PROGRESS"]

        # Add waiting state(s)
        if random.random() < 0.55:
            steps.append(random.choice(list(WAIT_STATUSES)))
            steps.append("IN_PROGRESS")

        # Add a second blockage sometimes
        if random.random() < 0.20:
            steps.append("BLOCKED")
            steps.append("IN_PROGRESS")

        steps += ["RESOLVED", "CLOSED"]

        # Allocate durations across steps
        remaining_seconds = (resolved_at - created_at).total_seconds()
        weights = np.random.dirichlet(np.ones(len(steps)))
        durations = (weights * remaining_seconds).astype(int)

        # Ensure each step has at least 60 seconds
        durations = np.maximum(durations, 60)

        # Team assignment across lifecycle (introduce realistic handoffs)
        assigned_team = initial_team

        # Handoff probability depends on priority (lower priority -> more likely to be handed off)
        handoff_prob = {"P0": 0.05, "P1": 0.12, "P2": 0.22, "P3": 0.30}[priority]

        t = created_at
        for status, dur in zip(steps, durations):
            status_start = t
            status_end = t + timedelta(seconds=int(dur))

            # Occasionally change assigned team at meaningful points
            if status in {"TRIAGE", "IN_PROGRESS"} and random.random() < handoff_prob:
                # pick a different team
                assigned_team = random.choice([x for x in teams if x != assigned_team])

            history_rows.append(
                {
                    "ticket_id": ticket_id,
                    "status": status,
                    "status_start": status_start.isoformat(),
                    "status_end": status_end.isoformat(),
                    "assigned_team": assigned_team,
                }
            )
            t = status_end

        tickets_rows.append(
            {
                "ticket_id": ticket_id,
                "created_at": created_at.isoformat(),
                "resolved_at": resolved_at.isoformat(),
                "priority": priority,
                "team_id": initial_team,
                "category": category,
            }
        )

    tickets = pd.DataFrame(tickets_rows)
    status_history = pd.DataFrame(history_rows)
    return tickets, status_history


if __name__ == "__main__":
    tickets_df, history_df = generate_synthetic()
    tickets_df.to_csv("data/tickets.csv", index=False)
    history_df.to_csv("data/status_history.csv", index=False)
    print("✅ Wrote data/tickets.csv and data/status_history.csv")