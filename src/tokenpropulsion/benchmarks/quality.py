"""Task-specific deterministic output evaluators; no semantic-equivalence claims."""

import json
import math
from typing import Any


def _unique_object(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result = {}
    for key, value in pairs:
        if key in result:
            raise ValueError("duplicate JSON key")
        result[key] = value
    return result


def evaluate(output: str, expected: str, mode: str = "exact") -> bool:
    if mode == "exact":
        return output == expected
    if mode == "json":
        try:
            left = json.loads(output, object_pairs_hook=_unique_object)
            right = json.loads(expected, object_pairs_hook=_unique_object)
            # Canonical serialization distinguishes booleans from numbers and rejects NaN.
            return json.dumps(left, sort_keys=True, allow_nan=False) == json.dumps(
                right, sort_keys=True, allow_nan=False
            )
        except (ValueError, TypeError):
            return False
    raise ValueError("mode must be exact or json")


def validate_schema(value: Any, schema: dict[str, Any]) -> bool:
    """Small explicitly limited schema: object properties, required keys, scalar types.

    Reject unsupported keywords instead of silently ignoring constraints. For complete
    JSON Schema, supply an evaluator using a separately installed JSON Schema library.
    """
    if set(schema) - {"type", "properties", "required", "additionalProperties"}:
        raise ValueError("unsupported schema keyword")
    kind = schema.get("type")
    types: dict[str, type[Any] | tuple[type[Any], ...]] = {
        "string": str,
        "integer": int,
        "number": (int, float),
        "boolean": bool,
        "object": dict,
        "array": list,
        "null": type(None),
    }
    if kind not in types:
        raise ValueError("unsupported schema type")
    if kind != "object" and set(schema) - {"type"}:
        raise ValueError("object keywords on non-object schema")
    if not isinstance(value, types[kind]):
        return False
    if kind in {"integer", "number"} and isinstance(value, bool):
        return False
    if kind == "number" and isinstance(value, float) and not math.isfinite(value):
        return False
    if kind == "object":
        props = schema.get("properties", {})
        if not all(key in value for key in schema.get("required", [])):
            return False
        if schema.get("additionalProperties") is False and set(value) - set(props):
            return False
        return all(validate_schema(value[k], spec) for k, spec in props.items() if k in value)
    return True
