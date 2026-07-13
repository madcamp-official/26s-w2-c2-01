"""JSON cache helpers for the two volatility scan phases."""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Mapping

CACHE_DIR = Path(__file__).resolve().parent.parent.parent / "data"
DAILY_CANDIDATES_FILE = CACHE_DIR / "volatility_daily_candidates.json"
TODAY_RESULTS_FILE = CACHE_DIR / "volatility_today.json"


def write_json(path: Path, payload: Mapping[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    temporary.replace(path)


def read_json(path: Path) -> dict[str, Any] | None:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
        return payload if isinstance(payload, dict) else None
    except (FileNotFoundError, json.JSONDecodeError, OSError):
        return None


def cache_daily_candidates(candidates: Mapping[str, Any]) -> dict[str, Any]:
    payload = {"generated_at": datetime.now(timezone.utc).isoformat(), "candidates": dict(candidates)}
    write_json(DAILY_CANDIDATES_FILE, payload)
    return payload


def cache_today_results(results: Mapping[str, Any]) -> dict[str, Any]:
    payload = {"generated_at": datetime.now(timezone.utc).isoformat(), **dict(results)}
    write_json(TODAY_RESULTS_FILE, payload)
    return payload
