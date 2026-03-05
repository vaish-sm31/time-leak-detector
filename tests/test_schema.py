import pandas as pd
import pytest

from src.ingest import load_and_validate

from contracts.schema import validate_inputs


def test_schema_valid_inputs_pass():
    tickets, history = load_and_validate()
    # validate_inputs should raise on failure. If it returns something, that's fine too.
    validate_inputs(tickets, history)


def test_schema_missing_required_column_fails():
    tickets, history = load_and_validate()

    bad = tickets.drop(columns=["ticket_id"])
    with pytest.raises(Exception):
        validate_inputs(bad, history)


def test_schema_bad_timestamp_fails():
    tickets, history = load_and_validate()

    bad = history.copy()
    bad["status_start"] = bad["status_start"].astype("object")
    bad.loc[0, "status_start"] = "not-a-timestamp"
    with pytest.raises(Exception):
        validate_inputs(tickets, bad)