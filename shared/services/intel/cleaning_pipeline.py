"""
数据清洗管道

编排多个清洗器按顺序执行，处理采集到的原始数据。
管道流程：TextCleaner -> DedupCleaner -> EnricherCleaner
"""

import json
import logging
from datetime import datetime, timezone
from typing import Dict, List, Optional

from sqlalchemy import select

from shared.services.intel.cleaners.base import BaseCleaner

logger = logging.getLogger(__name__)


class CleaningPipeline:
    """
    数据清洗管道

    将多个清洗器串联执行，依次处理采集条目的内容和元数据。
    """

    def __init__(self, cleaners: Optional[List[BaseCleaner]] = None):
        self._cleaners: List[BaseCleaner] = cleaners or []

    def add_cleaner(self, cleaner: BaseCleaner) -> None:
        """添加清洗器到管道末尾"""
        self._cleaners.append(cleaner)
        logger.info(f"添加清洗器: {cleaner.name}")

    def remove_cleaner(self, name: str) -> bool:
        """按名称移除清洗器"""
        for i, c in enumerate(self._cleaners):
            if c.name == name:
                self._cleaners.pop(i)
                return True
        return False

    @property
    def cleaner_names(self) -> List[str]:
        return [c.name for c in self._cleaners]

    async def process_item(self, item_id: int, content: str, title: str = "", metadata: Optional[dict] = None) -> dict:
        """
        对单条采集条目执行完整清洗管道。

        Args:
            item_id: 采集条目 ID
            content: 原始内容
            title: 标题
            metadata: 元数据

        Returns:
            dict: {"content", "title", "metadata", "status"}
        """
        current_content = content
        current_title = title
        current_metadata = metadata or {}
        status = "cleaned"

        for cleaner in self._cleaners:
            try:
                result = await cleaner.clean(
                    item_id=item_id,
                    content=current_content,
                    title=current_title,
                    metadata=current_metadata,
                )
                current_content = result.get("content", current_content)
                current_title = result.get("title", current_title)
                current_metadata = result.get("metadata", current_metadata)

            except Exception as e:
                logger.error(f"清洗器 {cleaner.name} 处理条目 {item_id} 异常: {e}")
                status = "clean_error"
                break

        return {
            "content": current_content,
            "title": current_title,
            "metadata": current_metadata,
            "status": status,
        }

    async def process_source(self, source_id: int) -> Dict[str, int]:
        """
        处理指定数据源下所有状态为 raw 的采集条目。

        Args:
            source_id: 数据源 ID

        Returns:
            dict: {"processed", "success", "errors"}
        """
        from shared.models import CollectedItem
        from src.extensions import get_db

        stats = {"processed": 0, "success": 0, "errors": 0}

        with get_db() as db:
            items = db.execute(
                select(CollectedItem).where(
                    CollectedItem.source_id == source_id,
                    CollectedItem.status == "raw",
                )
            ).scalars().all()

            for item in items:
                try:
                    # 解析已有元数据
                    existing_meta = {}
                    if item.metadata_json:
                        try:
                            existing_meta = json.loads(item.metadata_json)
                        except json.JSONDecodeError:
                            pass

                    result = await self.process_item(
                        item_id=item.id,
                        content=item.content_raw or "",
                        title=item.title or "",
                        metadata=existing_meta,
                    )

                    # 更新数据库
                    item.content_cleaned = result["content"]
                    item.title = result["title"] or item.title
                    item.metadata_json = json.dumps(result["metadata"], ensure_ascii=False)
                    item.status = result["status"]

                    stats["success"] += 1

                except Exception as e:
                    logger.error(f"清洗条目 {item.id} 异常: {e}")
                    item.status = "clean_error"
                    stats["errors"] += 1

                stats["processed"] += 1

            db.commit()

        logger.info(
            f"清洗管道完成 source_id={source_id}: "
            f"processed={stats['processed']} success={stats['success']} errors={stats['errors']}"
        )
        return stats


def create_default_pipeline() -> CleaningPipeline:
    """创建默认清洗管道"""
    from shared.services.intel.cleaners.text_cleaner import TextCleaner
    from shared.services.intel.cleaners.dedup import DedupCleaner
    from shared.services.intel.cleaners.enricher import EnricherCleaner

    pipeline = CleaningPipeline()
    pipeline.add_cleaner(TextCleaner())
    pipeline.add_cleaner(DedupCleaner())
    pipeline.add_cleaner(EnricherCleaner(use_llm=False))
    return pipeline


# 全局实例
cleaning_pipeline = create_default_pipeline()
