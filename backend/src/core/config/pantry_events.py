from __future__ import annotations

from src.core.config.content_pool import load_pool, select_items


def get_pantry_events(
    pool_ids: list[str] | None = None,
    count: int = 0,
    seed_id: str = "",
) -> list[dict[str, str]]:
    """返回茶水间事件列表。

    无参数时从内容池加载全部条目（向后兼容 SCRIPTED_PANTRY_EVENTS）。
    传入 seed_id 时进行确定性选取。
    """
    if pool_ids or count:
        return select_items("pantry", pool_ids or [], count, seed_id)
    return load_pool("pantry")


# 向后兼容
SCRIPTED_PANTRY_EVENTS: list[dict[str, str]] = []


def _populate_pantry() -> None:
    global SCRIPTED_PANTRY_EVENTS
    items = load_pool("pantry")
    SCRIPTED_PANTRY_EVENTS = [
        {
            "time": item.get("time", ""),
            "title": item.get("title", ""),
            "content": item.get("content", ""),
        }
        for item in items
    ]


_populate_pantry()
