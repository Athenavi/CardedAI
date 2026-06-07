"""
采集引擎核心

CollectorEngine 是情报采集的中央协调器，负责：
1. 注册和管理各类型采集器
2. 执行采集任务（从 DataSource 到 CollectedItem）
3. 去重处理
4. 存储到数据库
5. 触发清洗管道
"""

import asyncio
import json
import logging
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Type

from sqlalchemy import select, and_

from shared.services.intel.collectors.base import BaseCollector, CollectedItemData

logger = logging.getLogger(__name__)

# 性能优化：采集任务队列（延迟导入避免循环依赖）
def _get_collection_queue():
    """延迟获取采集任务队列"""
    try:
        from shared.services.performance.engine_optimizer import get_collection_queue
        return get_collection_queue()
    except Exception:
        return None


class CollectorEngine:
    """
    采集引擎核心

    使用注册表模式管理采集器，类似插件系统的设计。
    """

    def __init__(self):
        self._collectors: Dict[str, BaseCollector] = {}

    def register_collector(self, collector: BaseCollector) -> None:
        """
        注册采集器。

        Args:
            collector: BaseCollector 子类实例
        """
        if not collector.source_type:
            raise ValueError(f"采集器 {collector.__class__.__name__} 未定义 source_type")
        self._collectors[collector.source_type] = collector
        logger.info(f"注册采集器: {collector.source_type} -> {collector.__class__.__name__}")

    def get_collector(self, source_type: str) -> Optional[BaseCollector]:
        """获取指定类型的采集器"""
        return self._collectors.get(source_type)

    @property
    def registered_types(self) -> List[str]:
        """返回已注册的采集器类型列表"""
        return list(self._collectors.keys())

    async def enqueue_collection(self, source_id: int) -> Optional[str]:
        """
        将采集任务入队（异步非阻塞）。

        使用 Redis Streams 任务队列，由消费者异步处理。
        当队列不可用时直接降级为同步执行。

        Args:
            source_id: 数据源 ID

        Returns:
            Redis 消息 ID（队列模式）或 None（直接执行模式）
        """
        collection_queue = _get_collection_queue()
        if collection_queue:
            try:
                from shared.services.performance.engine_optimizer import CollectionTask
                task = CollectionTask(source_id=source_id)
                msg_id = await collection_queue.enqueue(task)
                logger.info(f"采集任务已入队: source_id={source_id}, msg_id={msg_id}")
                return msg_id
            except Exception as e:
                logger.warning(f"采集任务入队失败，降级为直接执行: {e}")

        # 降级：直接执行
        await self.run_collection(source_id)
        return None

    async def process_queue(self, max_tasks: int = 10) -> Dict[str, Any]:
        """
        从任务队列消费并执行采集任务。

        适用于后台消费者进程调用。

        Args:
            max_tasks: 单次最多消费的任务数

        Returns:
            处理结果摘要
        """
        collection_queue = _get_collection_queue()
        if not collection_queue:
            logger.warning("采集队列不可用，跳过队列处理")
            return {"processed": 0}

        results = {"processed": 0, "success": 0, "failed": 0}
        tasks = await collection_queue.dequeue(count=max_tasks, block_ms=3000)

        for msg_id, task in tasks:
            try:
                result = await self.run_collection(task.source_id)
                await collection_queue.ack(msg_id)
                await collection_queue.report_result(task, {
                    "status": "completed",
                    "items_count": result.get("new", 0),
                })
                results["processed"] += 1
                results["success"] += 1
            except Exception as e:
                logger.error(f"队列采集任务执行失败 source_id={task.source_id}: {e}")
                await collection_queue.ack(msg_id)
                await collection_queue.report_result(task, {
                    "status": "failed",
                    "error": str(e),
                })
                results["processed"] += 1
                results["failed"] += 1

        return results

    async def run_collection(self, source_id: int) -> Dict[str, Any]:
        """
        执行一次完整采集任务。

        流程:
        1. 从数据库读取 DataSource 配置
        2. 根据 source_type 选择采集器
        3. 执行采集
        4. 去重
        5. 存储 CollectedItem 到数据库
        6. 更新 DataSource.last_collected_at
        7. 触发清洗管道

        Args:
            source_id: 数据源 ID

        Returns:
            Dict: 采集结果摘要 {total, new, skipped, errors}
        """
        from shared.models import DataSource, CollectedItem
        from src.extensions import get_db

        result = {"total": 0, "new": 0, "skipped": 0, "errors": 0}

        # 1. 读取 DataSource
        with get_db() as db:
            source = db.get(DataSource, source_id)
            if not source:
                logger.error(f"数据源不存在: {source_id}")
                return result

            if not source.is_active:
                logger.info(f"数据源已禁用: {source_id}")
                return result

            source_type = source.source_type
            url = source.url

            # 解析 config JSON
            try:
                config = json.loads(source.config) if source.config else {}
            except json.JSONDecodeError:
                config = {}

        # 2. 选择采集器
        collector = self.get_collector(source_type)
        if not collector:
            logger.error(f"未注册的采集器类型: {source_type}")
            return result

        # 3. 验证配置
        if not await collector.validate_config(config):
            logger.error(f"采集器配置验证失败: {source_id} ({source_type})")
            return result

        # 4. 执行采集
        try:
            items = await collector.collect(config, url)
        except Exception as e:
            logger.error(f"采集执行异常 source_id={source_id}: {e}")
            return result

        result["total"] = len(items)

        # 5. 去重 + 存储
        with get_db() as db:
            for item_data in items:
                try:
                    # 去重：检查 content_hash 是否已存在
                    if item_data.content_hash:
                        existing = db.execute(
                            select(CollectedItem).where(
                                and_(
                                    CollectedItem.source_id == source_id,
                                    CollectedItem.content_hash == item_data.content_hash,
                                )
                            )
                        ).scalar_one_or_none()

                        if existing:
                            result["skipped"] += 1
                            continue

                    # 存储新条目
                    new_item = CollectedItem(
                        source_id=source_id,
                        url=item_data.url,
                        title=item_data.title,
                        content_raw=item_data.content_raw,
                        content_hash=item_data.content_hash,
                        metadata_json=json.dumps(item_data.metadata, ensure_ascii=False) if item_data.metadata else None,
                        status="raw",
                        collected_at=datetime.now(timezone.utc),
                    )
                    db.add(new_item)
                    result["new"] += 1

                except Exception as e:
                    logger.error(f"存储采集条目异常: {e}")
                    result["errors"] += 1

            # 6. 更新采集时间
            try:
                source = db.get(DataSource, source_id)
                if source:
                    source.last_collected_at = datetime.now(timezone.utc)
            except Exception as e:
                logger.error(f"更新采集时间异常: {e}")

            # 7. 提交所有变更（采集条目 + 更新采集时间）
            db.commit()

        logger.info(
            f"采集完成 source_id={source_id} type={source_type}: "
            f"total={result['total']} new={result['new']} skipped={result['skipped']} errors={result['errors']}"
        )

        # 8. 触发清洗管道（如果有新条目）
        if result["new"] > 0:
            await self._trigger_cleaning(source_id)

        return result

    async def _trigger_cleaning(self, source_id: int) -> None:
        """触发数据清洗管道"""
        try:
            from shared.services.intel.cleaning_pipeline import cleaning_pipeline
            await cleaning_pipeline.process_source(source_id)
        except ImportError:
            logger.debug("清洗管道模块尚未实现，跳过")
        except Exception as e:
            logger.error(f"触发清洗管道异常: {e}")

    async def run_all_active(self, parallel: bool = True) -> Dict[str, Any]:
        """
        执行所有活跃数据源的采集。

        Args:
            parallel: 是否并行执行（默认 True，使用 asyncio.gather）

        Returns:
            Dict: {source_id: result, ...}
        """
        from shared.models import DataSource
        from src.extensions import get_db

        results = {}

        with get_db() as db:
            sources = db.execute(
                select(DataSource).where(DataSource.is_active == True)
            ).scalars().all()

            source_ids = [s.id for s in sources]

        if parallel and len(source_ids) > 1:
            # 并行采集所有数据源
            tasks = [self.run_collection(sid) for sid in source_ids]
            gathered = await asyncio.gather(*tasks, return_exceptions=True)
            for sid, res in zip(source_ids, gathered):
                if isinstance(res, Exception):
                    logger.error(f"并行采集异常 source_id={sid}: {res}")
                    results[sid] = {"total": 0, "new": 0, "skipped": 0, "errors": 1}
                else:
                    results[sid] = res
        else:
            for source_id in source_ids:
                results[source_id] = await self.run_collection(source_id)

        logger.info(f"全部采集完成: {len(results)} 个数据源 (parallel={parallel})")
        return results


# 全局实例
collector_engine = CollectorEngine()


def setup_default_collectors() -> None:
    """注册默认采集器（应用启动时调用）"""
    from shared.services.intel.collectors.rss_collector import RSSCollector
    from shared.services.intel.collectors.web_collector import WebCollector
    from shared.services.intel.collectors.api_collector import APICollector

    collector_engine.register_collector(RSSCollector())
    collector_engine.register_collector(WebCollector())
    collector_engine.register_collector(APICollector())

    logger.info(f"默认采集器已注册: {collector_engine.registered_types}")
