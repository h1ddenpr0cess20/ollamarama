from __future__ import annotations

from typing import List, Dict, Any


def add_numbers(numbers: List[float]) -> Dict[str, Any]:
    try:
        total = sum(float(n) for n in numbers)
    except Exception:
        return {"error": "Invalid 'numbers'; expected a list of numbers."}
    return {"result": float(total)}


def multiply_numbers(numbers: List[float]) -> Dict[str, Any]:
    try:
        result = 1.0
        for n in numbers:
            result *= float(n)
    except Exception:
        return {"error": "Invalid 'numbers'; expected a list of numbers."}
    return {"result": float(result)}
