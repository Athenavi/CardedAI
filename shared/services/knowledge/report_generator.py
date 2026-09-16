"""
AI 研报生成器

基于 RAG 检索的知识库内容，自动生成结构化研报。

生成流程：
1. RAG 检索相关知识
2. LLM 生成报告提纲（标题 + 章节列表）
3. 逐章节生成内容（每章节独立 RAG + LLM）
4. 汇总生成摘要
5. 格式化输出 Markdown
"""

import json
from datetime import datetime
from typing import Any, Dict, List, Optional
from dataclasses import dataclass, field

from src.unified_logger import default_logger as logger


@dataclass
class ReportSection:
    """报告章节"""
    title: str = ""
    content: str = ""
    order: int = 0


@dataclass
class ReportResult:
    """报告生成结果"""
    title: str = ""
    summary: str = ""
    sections: List[ReportSection] = field(default_factory=list)
    sources: List[Dict[str, Any]] = field(default_factory=list)
    markdown: str = ""
    generated_at: str = ""
    success: bool = True
    error: Optional[str] = None


class ReportGenerator:
    """
    AI 研报生成器

    利用 RAG 检索 + LLM 生成，自动撰写结构化研究报告。
    """

    def __init__(self):
        from shared.services.knowledge.rag_chain import rag_chain
        from shared.services.ai.llm_client import llm_client

        self.rag_chain = rag_chain
        self.llm_client = llm_client

    async def generate_report(
        self,
        topic: str,
        knowledge_base_id: int,
        template: str = "default",
        max_sections: int = 6,
        detail_level: str = "standard",
    ) -> ReportResult:
        """
        生成研报

        Args:
            topic: 报告主题
            knowledge_base_id: 知识库 ID
            template: 报告模板 (default/technical/market/risk)
            max_sections: 最大章节数
            detail_level: 详细程度 (brief/standard/detailed)

        Returns:
            ReportResult 生成结果
        """
        try:
            # 1. RAG 检索相关知识
            rag_result = await self.rag_chain.query(
                question=f"关于「{topic}」的所有相关信息、数据和分析",
                knowledge_base_id=knowledge_base_id,
                top_k=20,
                include_sources=True,
            )

            if not rag_result.success:
                return ReportResult(
                    success=False,
                    error=f"知识检索失败: {rag_result.error}",
                )

            sources = rag_result.sources
            context = self._build_context(sources)

            # 2. 生成提纲
            outline = await self._generate_outline(topic, context, template, max_sections)
            if not outline:
                return ReportResult(success=False, error="提纲生成失败")

            # 3. 逐章节生成
            sections = []
            for i, section_info in enumerate(outline.get("sections", [])):
                section = await self._generate_section(
                    topic=topic,
                    section_title=section_info.get("title", f"章节{i + 1}"),
                    section_description=section_info.get("description", ""),
                    context=context,
                    detail_level=detail_level,
                    order=i,
                )
                sections.append(section)

            # 4. 生成摘要
            summary = await self._generate_summary(topic, sections)

            # 5. 组装 Markdown
            markdown = self._format_markdown(
                title=outline.get("title", topic),
                summary=summary,
                sections=sections,
            )

            return ReportResult(
                title=outline.get("title", topic),
                summary=summary,
                sections=sections,
                sources=sources,
                markdown=markdown,
                generated_at=datetime.utcnow().isoformat(),
            )

        except Exception as e:
            logger.error(f"研报生成失败: {e}")
            return ReportResult(success=False, error=str(e))

    async def _generate_outline(
        self,
        topic: str,
        context: str,
        template: str,
        max_sections: int,
    ) -> Optional[Dict[str, Any]]:
        """LLM 生成报告提纲"""
        template_prompts = {
            "default": "通用研究报告",
            "technical": "技术分析报告",
            "market": "市场研究报告",
            "risk": "风险评估报告",
        }
        report_type = template_prompts.get(template, "研究报告")

        prompt = f"""基于以下参考资料，为「{topic}」生成一份{report_type}的提纲。

参考资料摘要：
{context[:3000]}

要求：
1. 报告标题要专业、简洁
2. 包含 {max_sections} 个主要章节
3. 每个章节包含标题和简要描述
4. 章节之间逻辑连贯，从概述到分析到结论

请以 JSON 格式返回：
{{
    "title": "报告标题",
    "sections": [
        {{"title": "章节标题", "description": "章节内容概述"}}
    ]
}}"""

        result = await self.llm_client.generate_json(
            prompt=prompt,
            system_prompt="你是一位专业的研究报告编辑，擅长设计报告结构和提纲。",
            temperature=0.4,
        )

        if result.get("success") and isinstance(result.get("content"), dict):
            return result["content"]

        # 降级方案：返回默认提纲
        logger.warning("提纲生成 JSON 解析失败，使用默认提纲")
        return {
            "title": f"关于「{topic}」的研究报告",
            "sections": [
                {"title": "概述", "description": "主题背景和研究目的"},
                {"title": "现状分析", "description": "当前状态和主要特征"},
                {"title": "关键发现", "description": "核心数据和重要发现"},
                {"title": "趋势与展望", "description": "未来发展趋势预判"},
                {"title": "结论与建议", "description": "总结观点和行动建议"},
            ][:max_sections],
        }

    async def _generate_section(
        self,
        topic: str,
        section_title: str,
        section_description: str,
        context: str,
        detail_level: str,
        order: int,
    ) -> ReportSection:
        """LLM 生成单个章节"""
        length_map = {
            "brief": "200-400字",
            "standard": "400-800字",
            "detailed": "800-1500字",
        }
        target_length = length_map.get(detail_level, "400-800字")

        prompt = f"""基于以下参考资料，撰写研究报告的一个章节。

报告主题：{topic}
章节标题：{section_title}
章节要求：{section_description}
目标长度：{target_length}

参考资料：
{context[:4000]}

要求：
1. 内容要有深度，引用具体数据和事实
2. 使用 Markdown 格式（支持标题、列表、粗体等）
3. 如有引用来源，在文中标注
4. 语言专业、客观、有条理

请直接输出章节内容（Markdown 格式），不要包含章节标题本身。"""

        result = await self.llm_client.generate_text(
            prompt=prompt,
            system_prompt="你是一位专业的研究报告撰写者，擅长基于数据撰写深度分析。",
            temperature=0.4,
            max_tokens=2000,
        )

        content = ""
        if result.get("success"):
            content = result.get("content", "")
        else:
            content = f"*（章节内容生成失败: {result.get('error', '未知错误')}）*"

        return ReportSection(
            title=section_title,
            content=content,
            order=order,
        )

    async def _generate_summary(self, topic: str, sections: List[ReportSection]) -> str:
        """LLM 生成报告摘要"""
        sections_text = "\n".join(
            f"## {s.title}\n{s.content[:200]}..." for s in sections
        )

        prompt = f"""基于以下研究报告的各章节内容，生成一份简洁的执行摘要。

报告主题：{topic}
各章节摘要：
{sections_text[:3000]}

要求：
1. 200-300字
2. 涵盖报告的核心发现和主要结论
3. 语言精练、有洞察力"""

        result = await self.llm_client.generate_text(
            prompt=prompt,
            system_prompt="你是一位专业的报告摘要撰写者。",
            temperature=0.3,
            max_tokens=500,
        )

        if result.get("success"):
            return result.get("content", "")

        return f"本报告围绕「{topic}」展开分析，共包含 {len(sections)} 个章节。"

    @staticmethod
    def _build_context(sources: List[Dict[str, Any]]) -> str:
        """从来源构建上下文文本"""
        parts = []
        for i, source in enumerate(sources):
            content = source.get("content", "")
            title = source.get("document_title", f"来源{i + 1}")
            score = source.get("score", 0)
            parts.append(f"[{title}] (相关度: {score:.2f}) {content}")
        return "\n\n".join(parts)

    @staticmethod
    def _format_markdown(
        title: str,
        summary: str,
        sections: List[ReportSection],
    ) -> str:
        """格式化为 Markdown"""
        parts = [
            f"# {title}\n",
            f"## 执行摘要\n\n{summary}\n",
            "---\n",
        ]
        for section in sorted(sections, key=lambda s: s.order):
            parts.append(f"## {section.title}\n\n{section.content}\n")

        parts.append(f"\n---\n*报告生成时间: {datetime.utcnow().strftime('%Y-%m-%d %H:%M UTC')}*")
        return "\n".join(parts)


# 全局单例
report_generator = ReportGenerator()
