from __future__ import annotations

from typing import Any, Dict, List, Tuple


def _flatten_numbers(obj: Any, prefix: str = "") -> Dict[str, float]:
    """
    Extract all numeric values from nested dict/list structures.
    Returns a map: "path.to.key" -> number
    """
    out: Dict[str, float] = {}

    if isinstance(obj, dict):
        for k, v in obj.items():
            path = f"{prefix}.{k}" if prefix else str(k)
            out.update(_flatten_numbers(v, path))
    elif isinstance(obj, list):
        for i, v in enumerate(obj):
            path = f"{prefix}[{i}]"
            out.update(_flatten_numbers(v, path))
    else:
        if isinstance(obj, (int, float)) and not isinstance(obj, bool):
            out[prefix] = float(obj)

    return out


def validate_numbers_used(
    llm_output: Dict[str, Any],
    payload: Dict[str, Any],
    tolerance: float = 1e-6,
) -> Tuple[bool, List[str]]:
    """
    Ensures that every numeric value in llm_output["executive_summary"]["numbers_used"]
    exists in payload["headline_metrics"] (the source of truth).

    Returns: (ok, errors)
    """
    errors: List[str] = []

    # 1) extract numbers from payload (source of truth)
    payload_nums = _flatten_numbers(payload)

    # 2) extract "numbers_used" from LLM output
    try:
        numbers_used = llm_output["executive_summary"]["numbers_used"]
    except KeyError:
        return False, ["Missing executive_summary.numbers_used in LLM output."]

    if not isinstance(numbers_used, dict):
        return False, ["executive_summary.numbers_used must be an object/dict."]

    llm_nums = _flatten_numbers(numbers_used)

    # 3) check each number matches SOME payload number value (within tolerance)
    payload_values = list(payload_nums.values())
    for path, val in llm_nums.items():
        if not any(abs(val - pv) <= tolerance for pv in payload_values):
            errors.append(
                f"Unsupported number at '{path}': {val} is not present in payload values."
            )

    return (len(errors) == 0), errors


def strip_numbers_used(llm_output: Dict[str, Any]) -> Dict[str, Any]:
    """
    Removes numbers_used entirely (fallback) if validation fails.
    """
    out = dict(llm_output)
    if "executive_summary" in out and isinstance(out["executive_summary"], dict):
        out["executive_summary"] = dict(out["executive_summary"])
        out["executive_summary"].pop("numbers_used", None)
    return out