from __future__ import annotations

from src.core.config.content_pool import load_pool, select_items


def get_incidents(
    pool_ids: list[str] | None = None,
    count: int = 0,
    seed_id: str = "",
) -> list[dict[str, str]]:
    """返回事件列表。

    无参数时从内容池加载全部条目（向后兼容 SCRIPTED_INCIDENTS）。
    传入 seed_id 时进行确定性选取。
    """
    if pool_ids or count:
        return select_items("incidents", pool_ids or [], count, seed_id)
    return load_pool("incidents")


# 向后兼容：引擎文件直接 import SCRIPTED_INCIDENTS
SCRIPTED_INCIDENTS: list[dict[str, str]] = []


def _populate_incidents() -> None:
    global SCRIPTED_INCIDENTS
    items = load_pool("incidents")
    SCRIPTED_INCIDENTS = [
        {
            "time": item.get("time", ""),
            "title": item.get("title", ""),
            "content": item.get("content", ""),
        }
        for item in items
    ]


_populate_incidents()
