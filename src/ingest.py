from __future__ import annotations

import pandas as pd

from contracts.schema import validate_inputs


def load_and_validate() -> tuple[pd.DataFrame, pd.DataFrame]:
    tickets = pd.read_csv("data/tickets.csv")
    history = pd.read_csv("data/status_history.csv")

    # Validate + standardize datetimes (done inside validate_inputs)
    tickets, history = validate_inputs(tickets, history)

    return tickets, history


if __name__ == "__main__":
    t, h = load_and_validate()
    print("Tickets:", len(t))
    print("Status rows:", len(h))