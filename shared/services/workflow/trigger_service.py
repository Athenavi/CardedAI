"""
工作流触发器服务

支持三种触发方式：
- Cron 定时触发（复用 APScheduler）
- Webhook HTTP 触发
- Event 事件触发（复用插件 Hook 系统）

手动触发直接通过 API 调用 dag_engine.execute()。
"""

import asyncio
import json
from datetime import datetime, timezone
from typing import Any, Callable, Dict, List, Optional

from src.unified_logger import default_logger as logger


class TriggerService:
    """工作流触发器服务

    管理 cron / event / webhook 类型的触发器注册与调度。
    """

    def __init__(self):
        # workflow_id -> job metadata
        self._cron_jobs: Dict[int, Dict[str, Any]] = {}
        # event_name -> [callback, ...]
        self._event_handlers: Dict[str, List[Callable]] = {}
        # webhook_token -> workflow_id
        self._webhook_tokens: Dict[str, int] = {}
        # APScheduler 实例（延迟初始化）
        self._scheduler = None

    # ------------------------------------------------------------------
    # Cron 定时触发
    # ------------------------------------------------------------------

    async def register_cron_trigger(
        self,
        workflow_id: int,
        cron_expr: str,
        graph_data: Any = None,
        input_data: Optional[Dict] = None,
    ) -> Dict[str, Any]:
        """注册定时触发器

        Args:
            workflow_id: 工作流定义 ID
            cron_expr: Cron 表达式，支持标准 5 段式 (分 时 日 月 周)
            graph_data: 工作流图结构（用于直接执行）
            input_data: 默认输入数据

        Returns:
            {"job_id": str, "next_run_time": str}
        """
        scheduler = await self._get_scheduler()

        if scheduler is None:
            logger.warning("[TriggerService] APScheduler 不可用，记录 cron 配置但不激活")
            self._cron_jobs[workflow_id] = {
                "cron_expr": cron_expr,
                "graph_data": graph_data,
                "input_data": input_data,
                "active": False,
                "registered_at": datetime.now(timezone.utc).isoformat(),
            }
            return {
                "job_id": f"cron_{workflow_id}",
                "next_run_time": None,
                "warning": "APScheduler 不可用，触发器未激活",
            }

        # 解析 cron 表达式
        cron_parts = self._parse_cron(cron_expr)

        job_id = f"workflow_cron_{workflow_id}"

        # 移除旧任务
        try:
            existing = scheduler.get_job(job_id)
            if existing:
                scheduler.remove_job(job_id)
        except Exception:
            pass

        # 添加新任务
        scheduler.add_job(
            self._cron_callback,
            trigger="cron",
            id=job_id,
            args=[workflow_id, graph_data, input_data],
            **cron_parts,
            replace_existing=True,
        )

        self._cron_jobs[workflow_id] = {
            "job_id": job_id,
            "cron_expr": cron_expr,
            "active": True,
            "registered_at": datetime.now(timezone.utc).isoformat(),
        }

        job = scheduler.get_job(job_id)
        next_run = job.next_run_time.isoformat() if job and job.next_run_time else None

        logger.info(f"[TriggerService] 注册 cron 触发器: workflow={workflow_id}, cron={cron_expr}")
        return {"job_id": job_id, "next_run_time": next_run}

    async def unregister_cron_trigger(self, workflow_id: int) -> bool:
        """取消注册定时触发器"""
        scheduler = await self._get_scheduler()
        job_id = f"workflow_cron_{workflow_id}"

        if scheduler:
            try:
                scheduler.remove_job(job_id)
            except Exception:
                pass

        self._cron_jobs.pop(workflow_id, None)
        logger.info(f"[TriggerService] 取消 cron 触发器: workflow={workflow_id}")
        return True

    async def _cron_callback(
        self,
        workflow_id: int,
        graph_data: Any = None,
        input_data: Optional[Dict] = None,
    ) -> None:
        """Cron 触发回调"""
        try:
            logger.info(f"[TriggerService] Cron 触发工作流 {workflow_id}")
            # 更新最后触发时间
            if workflow_id in self._cron_jobs:
                self._cron_jobs[workflow_id]["last_fired_at"] = datetime.now(timezone.utc).isoformat()

            # 从数据库加载图结构（如果没有直接传入）
            if graph_data is None:
                graph_data = await self._load_graph_from_db(workflow_id)
                if graph_data is None:
                    logger.error(f"[TriggerService] 无法加载工作流 {workflow_id} 的图结构")
                    return

            # 保存执行记录到数据库
            execution_id = await self._create_execution_record(workflow_id, "scheduled")

            # 执行工作流
            from shared.services.workflow.dag_engine import dag_engine
            result = await dag_engine.execute(
                workflow_id=workflow_id,
                graph_data=graph_data,
                input_data=input_data or {},
                trigger_type="scheduled",
            )

            # 更新执行记录
            await self._update_execution_record(execution_id, result)

            logger.info(
                f"[TriggerService] 工作流 {workflow_id} 定时执行完成: "
                f"status={result.status}"
            )
        except Exception as exc:
            logger.error(f"[TriggerService] Cron 触发执行失败: {exc}")

    # ------------------------------------------------------------------
    # Event 事件触发
    # ------------------------------------------------------------------

    async def register_event_trigger(
        self,
        workflow_id: int,
        event_name: str,
        graph_data: Any = None,
        input_data: Optional[Dict] = None,
    ) -> Dict[str, Any]:
        """注册事件触发器

        当指定事件发生时自动触发工作流执行。

        Args:
            workflow_id: 工作流定义 ID
            event_name: 事件名称（如 'data_collected', 'alert_fired', 'article_published'）
            graph_data: 工作流图结构
            input_data: 默认输入数据

        Returns:
            {"event_name": str, "workflow_id": int, "registered": True}
        """

        async def _event_handler(event_data: Dict = None):
            """事件触发回调"""
            try:
                logger.info(f"[TriggerService] 事件 '{event_name}' 触发工作流 {workflow_id}")

                merged_input = {}
                if input_data:
                    merged_input.update(input_data)
                if event_data:
                    merged_input["__event__"] = event_data

                wf_graph = graph_data
                if wf_graph is None:
                    wf_graph = await self._load_graph_from_db(workflow_id)
                    if wf_graph is None:
                        logger.error(f"[TriggerService] 无法加载工作流 {workflow_id}")
                        return

                execution_id = await self._create_execution_record(workflow_id, "event")

                from shared.services.workflow.dag_engine import dag_engine
                result = await dag_engine.execute(
                    workflow_id=workflow_id,
                    graph_data=wf_graph,
                    input_data=merged_input,
                    trigger_type="event",
                )

                await self._update_execution_record(execution_id, result)
                logger.info(f"[TriggerService] 事件触发完成: workflow={workflow_id}, status={result.status}")
            except Exception as exc:
                logger.error(f"[TriggerService] 事件触发执行失败: {exc}")

        if event_name not in self._event_handlers:
            self._event_handlers[event_name] = []
        self._event_handlers[event_name].append(_event_handler)

        logger.info(f"[TriggerService] 注册事件触发器: event='{event_name}' -> workflow={workflow_id}")
        return {"event_name": event_name, "workflow_id": workflow_id, "registered": True}

    async def unregister_event_trigger(self, workflow_id: int, event_name: str) -> bool:
        """取消注册事件触发器"""
        handlers = self._event_handlers.get(event_name, [])
        # 简单实现：清空该事件的所有处理器（生产环境应标记 workflow_id）
        self._event_handlers[event_name] = [
            h for h in handlers
            if not getattr(h, "_workflow_id", None) == workflow_id
        ]
        logger.info(f"[TriggerService] 取消事件触发器: event='{event_name}', workflow={workflow_id}")
        return True

    async def emit_event(self, event_name: str, event_data: Dict = None) -> Dict[str, Any]:
        """触发事件，执行所有注册的事件处理器

        Args:
            event_name: 事件名称
            event_data: 事件附加数据

        Returns:
            {"event_name": str, "handlers_executed": int}
        """
        handlers = self._event_handlers.get(event_name, [])
        if not handlers:
            logger.debug(f"[TriggerService] 事件 '{event_name}' 无处理器")
            return {"event_name": event_name, "handlers_executed": 0}

        tasks = [h(event_data) for h in handlers]
        results = await asyncio.gather(*tasks, return_exceptions=True)

        errors = [str(r) for r in results if isinstance(r, Exception)]
        if errors:
            logger.warning(f"[TriggerService] 事件 '{event_name}' 处理中发生 {len(errors)} 个错误")

        return {
            "event_name": event_name,
            "handlers_executed": len(handlers),
            "errors": errors,
        }

    # ------------------------------------------------------------------
    # Webhook 触发
    # ------------------------------------------------------------------

    async def register_webhook_trigger(
        self,
        workflow_id: int,
        token: Optional[str] = None,
        graph_data: Any = None,
        input_data: Optional[Dict] = None,
    ) -> Dict[str, Any]:
        """注册 Webhook 触发器

        通过 HTTP POST 调用 /api/v2/workflow/webhooks/{token} 触发执行。

        Args:
            workflow_id: 工作流定义 ID
            token: Webhook token（不传则自动生成）
            graph_data: 工作流图结构
            input_data: 默认输入数据

        Returns:
            {"token": str, "webhook_url": str}
        """
        import uuid
        if token is None:
            token = uuid.uuid4().hex[:16]

        self._webhook_tokens[token] = workflow_id

        # 存储关联数据
        self._cron_jobs[f"webhook_{workflow_id}"] = {
            "token": token,
            "graph_data": graph_data,
            "input_data": input_data,
            "type": "webhook",
        }

        logger.info(f"[TriggerService] 注册 Webhook 触发器: workflow={workflow_id}, token={token}")
        return {
            "token": token,
            "workflow_id": workflow_id,
            "webhook_url": f"/api/v2/workflow/webhooks/{token}",
        }

    async def trigger_by_webhook(self, token: str, payload: Dict = None) -> Dict[str, Any]:
        """通过 Webhook token 触发工作流

        Args:
            token: Webhook token
            payload: HTTP 请求体

        Returns:
            ExecutionResult 字典
        """
        workflow_id = self._webhook_tokens.get(token)
        if workflow_id is None:
            raise ValueError(f"无效的 Webhook token: {token}")

        meta = self._cron_jobs.get(f"webhook_{workflow_id}", {})
        graph_data = meta.get("graph_data")
        input_data = meta.get("input_data", {})

        if payload:
            input_data["__webhook__"] = payload

        logger.info(f"[TriggerService] Webhook 触发工作流 {workflow_id}")

        if graph_data is None:
            graph_data = await self._load_graph_from_db(workflow_id)
            if graph_data is None:
                raise ValueError(f"无法加载工作流 {workflow_id}")

        execution_id = await self._create_execution_record(workflow_id, "webhook")

        from shared.services.workflow.dag_engine import dag_engine
        result = await dag_engine.execute(
            workflow_id=workflow_id,
            graph_data=graph_data,
            input_data=input_data,
            trigger_type="webhook",
        )

        await self._update_execution_record(execution_id, result)

        return result.to_dict()

    # ------------------------------------------------------------------
    # 手动触发
    # ------------------------------------------------------------------

    async def trigger_workflow(
        self,
        workflow_id: int,
        input_data: Optional[Dict] = None,
    ) -> Dict[str, Any]:
        """手动/自动触发工作流执行

        Args:
            workflow_id: 工作流定义 ID
            input_data: 输入数据

        Returns:
            ExecutionResult 字典
        """
        graph_data = await self._load_graph_from_db(workflow_id)
        if graph_data is None:
            raise ValueError(f"工作流 {workflow_id} 不存在或图结构为空")

        execution_id = await self._create_execution_record(workflow_id, "manual")

        from shared.services.workflow.dag_engine import dag_engine
        result = await dag_engine.execute(
            workflow_id=workflow_id,
            graph_data=graph_data,
            input_data=input_data or {},
            trigger_type="manual",
        )

        await self._update_execution_record(execution_id, result)

        # 如果配置了执行完成通知
        await self._check_notify_on_complete(workflow_id, result)

        return result.to_dict()

    # ------------------------------------------------------------------
    # 触发器管理
    # ------------------------------------------------------------------

    def get_all_triggers(self) -> List[Dict[str, Any]]:
        """获取所有已注册的触发器"""
        triggers = []

        for wf_id, meta in self._cron_jobs.items():
            if isinstance(wf_id, int):
                triggers.append({
                    "workflow_id": wf_id,
                    "trigger_type": "cron",
                    "config": meta,
                    "active": meta.get("active", False),
                })

        for event_name, handlers in self._event_handlers.items():
            triggers.append({
                "event_name": event_name,
                "trigger_type": "event",
                "handler_count": len(handlers),
                "active": True,
            })

        for token, wf_id in self._webhook_tokens.items():
            triggers.append({
                "workflow_id": wf_id,
                "trigger_type": "webhook",
                "token": token,
                "active": True,
            })

        return triggers

    # ------------------------------------------------------------------
    # 内部辅助
    # ------------------------------------------------------------------

    async def _get_scheduler(self):
        """延迟获取 APScheduler 实例"""
        if self._scheduler is not None:
            return self._scheduler

        try:
            from src.scheduler import scheduler
            self._scheduler = scheduler
            return scheduler
        except ImportError:
            logger.warning("[TriggerService] 无法导入 APScheduler scheduler")
            return None
        except Exception as exc:
            logger.warning(f"[TriggerService] 获取 scheduler 失败: {exc}")
            return None

    @staticmethod
    def _parse_cron(cron_expr: str) -> Dict[str, Any]:
        """解析 cron 表达式为 APScheduler cron trigger 参数

        支持标准 5 段式: 分 时 日 月 周
        """
        parts = cron_expr.strip().split()
        if len(parts) < 5:
            raise ValueError(f"无效的 cron 表达式: {cron_expr}（需要 5 段: 分 时 日 月 周）")

        return {
            "minute": parts[0],
            "hour": parts[1],
            "day": parts[2],
            "month": parts[3],
            "day_of_week": parts[4],
        }

    async def _load_graph_from_db(self, workflow_id: int) -> Optional[Any]:
        """从数据库加载工作流图结构"""
        try:
            from src.extensions import get_db
            from shared.models.workflow.workflow_definition import WorkflowDefinition

            with get_db() as db:
                wf = db.get(WorkflowDefinition, workflow_id)
                if wf and wf.graph:
                    return wf.graph  # JSON 字符串，dag_engine 会自动解析
            return None
        except Exception as exc:
            logger.error(f"[TriggerService] 加载工作流 {workflow_id} 失败: {exc}")
            return None

    async def _create_execution_record(self, workflow_id: int, trigger_type: str) -> Optional[int]:
        """创建执行记录"""
        try:
            from datetime import datetime, timezone
            from src.extensions import get_db
            from shared.models.workflow.workflow_execution import WorkflowExecution

            with get_db() as db:
                execution = WorkflowExecution(
                    workflow_id=workflow_id,
                    status="running",
                    trigger_type=trigger_type,
                    created_at=datetime.now(timezone.utc),
                    started_at=datetime.now(timezone.utc),
                )
                db.add(execution)
                db.flush()
                return execution.id
        except Exception as exc:
            logger.warning(f"[TriggerService] 创建执行记录失败: {exc}")
            return None

    async def _update_execution_record(
        self, execution_id: Optional[int], result
    ) -> None:
        """更新执行记录"""
        if execution_id is None:
            return

        try:
            from src.extensions import get_db
            from shared.models.workflow.workflow_execution import WorkflowExecution

            with get_db() as db:
                execution = db.get(WorkflowExecution, execution_id)
                if execution:
                    execution.status = result.status
                    execution.output_data = json.dumps(
                        result.output_data, ensure_ascii=False, default=str
                    ) if result.output_data else None
                    execution.error_message = result.error_message
                    execution.completed_at = result.completed_at
                    db.flush()
        except Exception as exc:
            logger.warning(f"[TriggerService] 更新执行记录失败: {exc}")

    async def _check_notify_on_complete(self, workflow_id: int, result) -> None:
        """检查并发送执行完成通知"""
        try:
            from src.extensions import get_db
            from shared.models.workflow.workflow_definition import WorkflowDefinition

            with get_db() as db:
                wf = db.get(WorkflowDefinition, workflow_id)
                if wf and wf.trigger_config:
                    config = json.loads(wf.trigger_config)
                    if config.get("notify_on_complete"):
                        logger.info(
                            f"[TriggerService] 工作流 {workflow_id} 执行完成, "
                            f"status={result.status}"
                        )
        except Exception as exc:
            logger.debug(f"[TriggerService] 通知检查失败: {exc}")


# 全局单例
trigger_service = TriggerService()
