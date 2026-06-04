"""
自然语言内容管理服务

提供基于自然语言的内容管理功能，支持意图识别、参数提取和批量操作

功能:
1. NLP 指令解析器
2. 意图识别（创建/更新/删除/查询）
3. 参数提取和验证
4. 批量操作支持
5. 操作历史回滚
"""

import re
from datetime import datetime
from enum import Enum
from typing import Dict, Any, List, Optional, Tuple


class IntentType(Enum):
    """意图类型"""
    CREATE = "create"
    UPDATE = "update"
    DELETE = "delete"
    QUERY = "query"
    PUBLISH = "publish"
    DRAFT = "draft"
    SEARCH = "search"
    BATCH = "batch"


class NLPCommandParser:
    """
    NLP 命令解析器

    将自然语言指令转换为结构化操作
    """

    def __init__(self):
        # 意图关键词映射
        self.intent_patterns = {
            IntentType.CREATE: [
                r'创建|新建|添加|发布',
                r'create|new|add|publish',
            ],
            IntentType.UPDATE: [
                r'更新|修改|编辑|更改',
                r'update|edit|modify|change',
            ],
            IntentType.DELETE: [
                r'删除|移除|去掉',
                r'delete|remove|drop',
            ],
            IntentType.QUERY: [
                r'查询|查看|显示|列出',
                r'query|view|show|list',
            ],
            IntentType.PUBLISH: [
                r'发布|上线',
                r'publish|go live',
            ],
            IntentType.DRAFT: [
                r'保存草稿|存为草稿',
                r'save draft|draft',
            ],
            IntentType.SEARCH: [
                r'搜索|查找|找',
                r'search|find|look for',
            ],
            IntentType.BATCH: [
                r'批量|全部|所有',
                r'batch|all|bulk',
            ],
        }

        # 实体提取模式
        self.entity_patterns = {
            'article': r'文章|帖子|post|article',
            'category': r'分类|类别|category',
            'tag': r'标签|tag',
            'user': r'用户|user',
            'comment': r'评论|comment',
            'media': r'图片|媒体|media|image',
        }

        # 时间表达式模式
        self.time_patterns = {
            'today': r'今天|今日|today',
            'yesterday': r'昨天|yesterday',
            'this_week': r'本周|这周|this week',
            'last_week': r'上周|last week',
            'this_month': r'本月|这个月|this month',
        }

    def parse_command(self, command: str) -> Dict[str, Any]:
        """
        解析自然语言命令

        Args:
            command: 自然语言命令

        Returns:
            解析结果，包含意图、实体、参数等
        """
        result = {
            "original_command": command,
            "intent": None,
            "entity_type": None,
            "parameters": {},
            "confidence": 0.0,
            "timestamp": datetime.now().isoformat(),
        }

        # 识别意图
        intent, intent_confidence = self._detect_intent(command)
        result["intent"] = intent.value if intent else None
        result["confidence"] = intent_confidence

        if not intent:
            result["error"] = "无法识别意图"
            return result

        # 提取实体类型
        entity_type = self._extract_entity_type(command)
        result["entity_type"] = entity_type

        # 提取参数
        parameters = self._extract_parameters(command, intent, entity_type)
        result["parameters"] = parameters

        return result

    def _detect_intent(self, command: str) -> Tuple[Optional[IntentType], float]:
        """检测意图"""
        best_intent = None
        best_confidence = 0.0

        for intent, patterns in self.intent_patterns.items():
            for pattern in patterns:
                if re.search(pattern, command, re.IGNORECASE):
                    # 计算置信度（基于匹配次数）
                    matches = len(re.findall(pattern, command, re.IGNORECASE))
                    confidence = min(matches * 0.3 + 0.5, 1.0)

                    if confidence > best_confidence:
                        best_intent = intent
                        best_confidence = confidence

        return best_intent, best_confidence

    def _extract_entity_type(self, command: str) -> Optional[str]:
        """提取实体类型"""
        for entity_type, pattern in self.entity_patterns.items():
            if re.search(pattern, command, re.IGNORECASE):
                return entity_type
        return None

    def _extract_parameters(
            self,
            command: str,
            intent: IntentType,
            entity_type: Optional[str]
    ) -> Dict[str, Any]:
        """提取参数"""
        params = {}

        # 提取标题
        title_match = re.search(r'["「](.+?)["」]', command)
        if title_match:
            params["title"] = title_match.group(1)

        # 提取数量
        count_match = re.search(r'(\d+)\s*(篇|个|条)', command)
        if count_match:
            params["count"] = int(count_match.group(1))

        # 提取时间范围
        for time_key, pattern in self.time_patterns.items():
            if re.search(pattern, command, re.IGNORECASE):
                params["time_range"] = time_key
                break

        # 提取状态
        if re.search(r'草稿|draft', command, re.IGNORECASE):
            params["status"] = "draft"
        elif re.search(r'发布|published', command, re.IGNORECASE):
            params["status"] = "published"

        # 提取分类
        category_match = re.search(r'分类[：:]\s*(\S+)', command)
        if category_match:
            params["category"] = category_match.group(1)

        # 提取标签
        tags_match = re.search(r'标签[：:]\s*(\S+)', command)
        if tags_match:
            params["tags"] = tags_match.group(1).split(',')

        # 提取搜索关键词
        if intent == IntentType.SEARCH:
            search_match = re.search(r'搜索\s+(.+)', command)
            if search_match:
                params["query"] = search_match.group(1).strip()

        return params


class BatchOperationManager:
    """
    批量操作管理器

    支持批量执行内容管理操作
    """

    def __init__(self):
        self.operation_history: List[Dict[str, Any]] = []

    async def execute_batch_operation(
            self,
            operation_type: str,
            items: List[Dict[str, Any]],
            parameters: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        执行批量操作

        Args:
            operation_type: 操作类型 (publish/draft/delete/update)
            items: 要操作的项目列表
            parameters: 操作参数

        Returns:
            操作结果
        """
        results = {
            "success": True,
            "total": len(items),
            "succeeded": 0,
            "failed": 0,
            "details": [],
            "operation_id": datetime.now().strftime("%Y%m%d%H%M%S"),
        }

        for item in items:
            try:
                # 执行单个操作
                result = await self._execute_single_operation(
                    operation_type,
                    item,
                    parameters
                )

                if result["success"]:
                    results["succeeded"] += 1
                else:
                    results["failed"] += 1

                results["details"].append(result)

            except Exception as e:
                results["failed"] += 1
                results["details"].append({
                    "item_id": item.get("id"),
                    "success": False,
                    "error": str(e)
                })

        # 记录操作历史
        self.operation_history.append({
            "operation_id": results["operation_id"],
            "type": operation_type,
            "timestamp": datetime.now().isoformat(),
            "results": results
        })

        return results

    async def _execute_single_operation(
            self,
            operation_type: str,
            item: Dict[str, Any],
            parameters: Dict[str, Any]
    ) -> Dict[str, Any]:
        """执行单个操作"""
        # 根据操作类型调用相应的服务
        try:
            item_id = item.get("id")
            if not item_id:
                return {"item_id": None, "success": False, "error": "Missing item id"}

            if operation_type in ("update", "edit"):
                # 更新操作
                update_data = {k: v for k, v in parameters.items() if k not in ("operation_type",)}
                update_data.update({k: v for k, v in item.items() if k != "id"})
                if update_data:
                    from shared.services.articles.article_manager.service import update_article
                    from src.utils.database.unified_manager import get_db_session
                    async with get_db_session() as db:
                        await update_article(db, item_id, **update_data)
                    return {"item_id": item_id, "success": True, "message": "update completed"}
            elif operation_type in ("delete", "remove"):
                from shared.services.articles.article_manager.service import delete_article
                from src.utils.database.unified_manager import get_db_session
                async with get_db_session() as db:
                    await delete_article(db, item_id)
                return {"item_id": item_id, "success": True, "message": "delete completed"}
            elif operation_type in ("publish",):
                from shared.services.articles.article_manager.service import update_article
                from src.utils.database.unified_manager import get_db_session
                async with get_db_session() as db:
                    await update_article(db, item_id, status=1)
                return {"item_id": item_id, "success": True, "message": "publish completed"}
            elif operation_type in ("unpublish",):
                from shared.services.articles.article_manager.service import update_article
                from src.utils.database.unified_manager import get_db_session
                async with get_db_session() as db:
                    await update_article(db, item_id, status=0)
                return {"item_id": item_id, "success": True, "message": "unpublish completed"}
            else:
                return {"item_id": item_id, "success": False, "error": f"Unsupported operation: {operation_type}"}
        except Exception as e:
            return {"item_id": item.get("id"), "success": False, "error": str(e)}

    def get_operation_history(self, limit: int = 10) -> List[Dict[str, Any]]:
        """获取操作历史"""
        return self.operation_history[-limit:]

    async def rollback_operation(self, operation_id: str) -> Dict[str, Any]:
        """
        回滚操作

        Args:
            operation_id: 操作ID

        Returns:
            回滚结果
        """
        # 查找操作记录
        operation = None
        for op in self.operation_history:
            if op["operation_id"] == operation_id:
                operation = op
                break

        if not operation:
            return {
                "success": False,
                "error": f"Operation not found: {operation_id}"
            }

        # 实际回滚逻辑：对已成功的操作执行反向操作
        rolled_back = 0
        rollback_errors = []
        op_type = operation.get("type", "")
        details = operation.get("results", {}).get("details", [])

        for detail in details:
            if not detail.get("success"):
                continue
            item_id = detail.get("item_id")
            if not item_id:
                continue
            try:
                if op_type in ("delete", "remove"):
                    # 删除操作无法回滚，记录警告
                    rollback_errors.append(f"Cannot rollback delete for item {item_id}")
                elif op_type == "publish":
                    from shared.services.articles.article_manager.service import update_article
                    from src.utils.database.unified_manager import get_db_session
                    async with get_db_session() as db:
                        await update_article(db, item_id, status=0)
                    rolled_back += 1
                elif op_type == "unpublish":
                    from shared.services.articles.article_manager.service import update_article
                    from src.utils.database.unified_manager import get_db_session
                    async with get_db_session() as db:
                        await update_article(db, item_id, status=1)
                    rolled_back += 1
                else:
                    rollback_errors.append(f"Rollback not supported for operation: {op_type}")
            except Exception as e:
                rollback_errors.append(f"Rollback failed for item {item_id}: {str(e)}")

        return {
            "success": rolled_back > 0 or len(rollback_errors) == 0,
            "message": f"Operation {operation_id} rolled back",
            "rolled_back_items": rolled_back,
            "errors": rollback_errors,
        }


# 全局实例
nlp_parser = NLPCommandParser()
batch_manager = BatchOperationManager()
