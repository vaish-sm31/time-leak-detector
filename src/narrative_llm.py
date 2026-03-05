from __future__ import annotations

import json
import os
from typing import Any, Dict

from openai import OpenAI


def build_exec_payload(
    team_table,
    category_table,
    priority_table,
    status_table,
    original_cost: float,
    savings_low: float,
    savings_base: float,
    savings_high: float,
) -> Dict[str, Any]:
    """
    Keep this payload SMALL: only aggregates, no raw ticket tables.
    This keeps cost low and reduces hallucination surface area.
    """
    return {
        "headline_metrics": {
            "original_estimated_cost": round(float(original_cost), 2),
            "savings_range": {
                "low": round(float(savings_low), 2),
                "base": round(float(savings_base), 2),
                "high": round(float(savings_high), 2),
            },
        },
        "top_leakage": {
            "by_team_top5": team_table.head(5).to_dict(orient="records"),
            "by_category_top5": category_table.head(5).to_dict(orient="records"),
            "by_priority": priority_table.to_dict(orient="records"),
        },
        "workflow_bottlenecks": {
            "time_by_status_top8": status_table.head(8).to_dict(orient="records"),
        },
    }


def generate_executive_summary(payload: Dict[str, Any], model: str = "gpt-4o-mini") -> Dict[str, Any]:
    """
    Calls OpenAI Responses API and asks for STRICT JSON back.
    """
    api_key = os.environ.get("OPENAI_API_KEY")
    if not api_key:
        raise RuntimeError("OPENAI_API_KEY is not set. Run: export OPENAI_API_KEY='...'" )

    client = OpenAI(api_key=api_key)

    system_rules = """
You are an operations analytics assistant.
Return ONLY valid JSON with the exact keys requested. No markdown, no extra text.

Output JSON schema:
{
  "executive_summary": {
    "one_paragraph": "string",
    "top_drivers": ["string", "string", "string"],
    "recommended_interventions": ["string", "string", "string"],
    "numbers_used": {
      "original_estimated_cost": number,
      "savings_low": number,
      "savings_base": number,
      "savings_high": number
    }
  }
}

Rules:
- Use ONLY numbers provided in the input payload.
- If a number is not present, do NOT invent it.
- Keep top_drivers and recommended_interventions specific and measurable.
""".strip()

    resp = client.responses.create(
        model=model,
        input=[
            {"role": "system", "content": system_rules},
            {"role": "user", "content": f"INPUT_PAYLOAD_JSON:\n{json.dumps(payload)}"},
        ],
    )

    text = resp.output_text.strip()
    return json.loads(text)