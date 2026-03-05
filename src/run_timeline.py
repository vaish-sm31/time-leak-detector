from __future__ import annotations

from src.ingest import load_and_validate
from src.timeline import build_ticket_timeline


def main():
    tickets, history = load_and_validate()

    example_ticket = tickets.iloc[0]["ticket_id"]
    timeline = build_ticket_timeline(example_ticket, history)

    print(f"\nTimeline for {example_ticket}")
    print(timeline)


if __name__ == "__main__":
    main()