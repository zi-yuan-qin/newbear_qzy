from __future__ import annotations

from src.core.config.content_pool import load_pool, select_items

REPORT_TRIGGER_TIME = "18:00"

BIG_FIVE_LABELS: dict[str, str] = {
    "O": "开放性",
    "C": "尽责性",
    "E": "外向性",
    "A": "宜人性",
    "S": "情绪稳定性",
}


def get_report_templates(
    pool_ids: list[str] | None = None,
    count: int = 0,
    seed_id: str = "",
) -> list[dict[str, str]]:
    """返回报告模板列表。

    无参数时从内容池加载全部条目。
    传入 seed_id 时进行确定性选取。
    """
    if pool_ids or count:
        return select_items("reports", pool_ids or [], count, seed_id)
    return load_pool("reports")
