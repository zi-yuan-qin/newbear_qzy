"""内容池管理器 (BE-002) — 加载、筛选、确定性选取。"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any

_POOL_DIR = Path(__file__).resolve().parent

_CATEGORY_MAP: dict[str, Path] = {
    "incidents": _POOL_DIR / "incidents",
    "meetings": _POOL_DIR / "meetings",
    "pantry": _POOL_DIR / "pantry",
    "reports": _POOL_DIR / "reports",
}

_CACHE: dict[str, list[dict[str, Any]]] = {}


def load_pool(category: str) -> list[dict[str, Any]]:
    """Load all JSON entries for a given category from content_pool/<category>/*.json."""
    if category in _CACHE:
        return _CACHE[category]

    pool_dir = _CATEGORY_MAP.get(category)
    if pool_dir is None or not pool_dir.is_dir():
        return []

    items: list[dict[str, Any]] = []
    for json_file in sorted(pool_dir.glob("*.json")):
        try:
            with open(json_file, "r", encoding="utf-8") as f:
                data = json.load(f)
            if isinstance(data, dict) and "id" in data:
                items.append(data)
        except (json.JSONDecodeError, OSError):
            continue

    _CACHE[category] = items
    return items


def select_items(
    category: str,
    pool_ids: list[str],
    count: int,
    seed_id: str,
) -> list[dict[str, Any]]:
    """Select up to `count` items from a pool, deterministically based on `seed_id`.

    If `pool_ids` is empty, picks from the full category pool.
    Same `seed_id` always returns the same selection.
    """
    all_items = load_pool(category)
    if not all_items:
        return []

    if pool_ids:
        filtered = [item for item in all_items if item.get("id") in pool_ids]
    else:
        filtered = list(all_items)

    if not filtered:
        return []

    shuffled = _deterministic_shuffle(filtered, seed_id)
    return shuffled[:count]


def filter_by_conditions(
    items: list[dict[str, Any]],
    conditions: dict[str, Any],
) -> list[dict[str, Any]]:
    """Filter pool items by param_conditions matching.

    Supported condition keys: min/max_cash, min/max_runway_days, etc.
    If an item has no param_conditions, it always matches.
    """
    if not conditions:
        return items

    result = []
    for item in items:
        params = item.get("param_conditions", {})
        if not params:
            result.append(item)
            continue

        matched = True
        for key, threshold in params.items():
            if key not in conditions:
                continue
            value = conditions[key]
            if key.startswith("min_") and value < threshold:
                matched = False
                break
            if key.startswith("max_") and value > threshold:
                matched = False
                break
        if matched:
            result.append(item)

    return result


def _deterministic_shuffle(
    items: list[dict[str, Any]],
    seed_id: str,
) -> list[dict[str, Any]]:
    """Shuffle items deterministically based on seed_id hash."""
    seed_bytes = hashlib.sha256(seed_id.encode()).digest()
    indices = list(range(len(items)))

    for i in range(len(indices) - 1, 0, -1):
        byte_idx = (len(indices) - 1 - i) % len(seed_bytes)
        j = seed_bytes[byte_idx] % (i + 1)
        indices[i], indices[j] = indices[j], indices[i]

    return [items[idx] for idx in indices]
