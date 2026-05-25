from __future__ import annotations

from src.core.config.content_pool import load_pool, select_items


def get_meetings(
    pool_ids: list[str] | None = None,
    count: int = 0,
    seed_id: str = "",
) -> list[dict[str, str]]:
    """返回会议事件列表。

    无参数时从内容池加载全部条目（向后兼容 SCRIPTED_MEETINGS）。
    传入 seed_id 时进行确定性选取。
    """
    if pool_ids or count:
        return select_items("meetings", pool_ids or [], count, seed_id)
    return load_pool("meetings")


# 向后兼容
SCRIPTED_MEETINGS: list[dict[str, str]] = []


def _populate_meetings() -> None:
    global SCRIPTED_MEETINGS
    items = load_pool("meetings")
    SCRIPTED_MEETINGS = [
        {
            "time": item.get("time", ""),
            "title": item.get("title", ""),
            "content": item.get("content", ""),
        }
        for item in items
    ]


_populate_meetings()
