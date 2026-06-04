"""
AI 智能工作流引擎服务
负责处理 AI 辅助写作、SEO 优化建议及标签推荐等任务
"""
import json
from datetime import datetime
from typing import Dict, Any, Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from shared.models.ai_workflow import AIWorkflow
from src.utils.database.main import get_async_session


class AIWorkflowService:
    """AI 工作流核心服务类"""

    @staticmethod
    async def create_task(user_id: int, task_type: str, input_data: Dict[str, Any]) -> int:
        """创建一个新的 AI 工作流任务"""
        async for db in get_async_session():
            workflow = AIWorkflow(
                user_id=user_id,
                task_type=task_type,
                input_data=json.dumps(input_data),
                status="processing",
                created_at=datetime.utcnow()
            )
            db.add(workflow)
            await db.commit()
            return workflow.id

    @staticmethod
    async def complete_task(task_id: int, output_data: Dict[str, Any], model_used: str = "fastblog-ai-v1"):
        """标记任务完成并保存结果"""
        async for db in get_async_session():
            query = select(AIWorkflow).where(AIWorkflow.id == task_id)
            result = await db.execute(query)
            workflow = result.scalar_one_or_none()
            if workflow:
                workflow.output_data = json.dumps(output_data)
                workflow.model_used = model_used
                workflow.status = "completed"
                workflow.completed_at = datetime.utcnow()
                await db.commit()

    @staticmethod
    async def fail_task(task_id: int, error_message: str):
        """标记任务失败"""
        async for db in get_async_session():
            query = select(AIWorkflow).where(AIWorkflow.id == task_id)
            result = await db.execute(query)
            workflow = result.scalar_one_or_none()
            if workflow:
                workflow.status = "failed"
                workflow.error_message = error_message
                workflow.completed_at = datetime.utcnow()
                await db.commit()

    # --- 具体业务逻辑实现 (P0-3, P0-4, P0-5) ---

    async def assist_writing(self, user_id: int, context: str, instruction: str) -> Dict[str, Any]:
        """P0-3: AI 辅助写作 (续写/润色/翻译)"""
        task_id = await self.create_task(user_id, "writing_assist", {"context": context, "instruction": instruction})
        try:
            # 模拟 AI 处理逻辑（实际应调用 LLM API）
            generated_text = f"[AI Generated based on: {instruction}]\n{context[:50]}..."
            result = {"generated_text": generated_text, "word_count": len(generated_text)}
            await self.complete_task(task_id, result)
            return result
        except Exception as e:
            await self.fail_task(task_id, str(e))
            raise e

    async def optimize_seo(self, user_id: int, title: str, content: str) -> Dict[str, Any]:
        """P0-4: 自动 SEO 优化建议"""
        task_id = await self.create_task(user_id, "seo_optimize", {"title": title, "content": content})
        try:
            # 模拟 SEO 分析
            suggestions = {
                "meta_description": f"{title} - {content[:100]}...",
                "keywords": ["FastBlog", "Python", "CMS"],
                "readability_score": 85,
                "improvements": ["增加内部链接", "优化标题长度"]
            }
            await self.complete_task(task_id, suggestions)
            return suggestions
        except Exception as e:
            await self.fail_task(task_id, str(e))
            raise e

    async def recommend_tags(self, user_id: int, content: str) -> Dict[str, Any]:
        """P0-5: 智能标签与分类推荐"""
        task_id = await self.create_task(user_id, "tag_recommend", {"content": content})
        try:
            # 模拟标签提取
            tags = ["Technology", "Development", "AI"]
            await self.complete_task(task_id, {"recommended_tags": tags})
            return {"recommended_tags": tags}
        except Exception as e:
            await self.fail_task(task_id, str(e))
            raise e


# 全局实例
ai_workflow_service = AIWorkflowService()
