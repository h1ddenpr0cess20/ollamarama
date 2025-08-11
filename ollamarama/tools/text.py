from __future__ import annotations

from typing import Dict, Any


def word_count(text: str) -> Dict[str, Any]:
    if not isinstance(text, str) or not text.strip():
        return {"count": 0}
    # Split on whitespace; simple count
    return {"count": len(text.split())}
