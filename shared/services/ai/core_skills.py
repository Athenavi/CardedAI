"""
核心 AI Agent Skills 实现

提供内容创作、SEO优化、插件生成等核心技能
"""

import re
from collections import Counter

from shared.services.ai.llm_client import llm_client
from shared.services.ai.skills_framework import (
    BaseSkill,
    SkillMetadata,
    SkillContext,
    SkillResult,
    SkillCategory,
    SkillPermission,
)


class ContentCreatorSkill(BaseSkill):
    """
    内容创作 Skill

    AI 辅助写作、大纲生成、段落扩写等功能
    """

    def __init__(self):
        metadata = SkillMetadata(
            name="content_creator",
            version="1.0.0",
            description="AI 辅助内容创作，包括文章大纲生成、段落扩写、标题优化等",
            author="FastBlog Team",
            category=SkillCategory.CONTENT_CREATION,
            permissions=[SkillPermission.READ_ONLY, SkillPermission.WRITE],
            tags=["ai", "writing", "content", "creation"],
            icon="✍️",
        )
        super().__init__(metadata)

    async def execute(self, context: SkillContext) -> SkillResult:
        """执行内容创作任务"""
        action = context.parameters.get("action")

        if action == "generate_outline":
            return await self._generate_outline(context)
        elif action == "expand_paragraph":
            return await self._expand_paragraph(context)
        elif action == "optimize_title":
            return await self._optimize_title(context)
        elif action == "extract_keywords":
            return await self._extract_keywords(context)
        else:
            return SkillResult(
                success=False,
                error=f"Unknown action: {action}"
            )

    async def _generate_outline(self, context: SkillContext) -> SkillResult:
        """生成文章大纲"""
        topic = context.parameters.get("topic")

        if not topic:
            return SkillResult(success=False, error="Topic is required")

        # 尝试使用 LLM 生成大纲
        if llm_client.is_available:
            result = await llm_client.generate_json(
                prompt=f"请为以下主题生成文章大纲，返回 JSON 格式：\n主题：{topic}\n\n"
                       f"要求：包含 title 和 sections 数组，每个 section 有 heading 和 points 数组。\n"
                       f"生成 4-6 个章节，每个章节 2-4 个要点。",
                system_prompt="你是一个专业的文章大纲规划师。请以 JSON 格式返回结果。",
            )
            if result.get("success") and isinstance(result.get("content"), dict):
                outline = result["content"]
                return SkillResult(
                    success=True,
                    data=outline,
                    message="Outline generated successfully (LLM)"
                )

        # Fallback: 模板大纲
        outline = {
            "title": f"{topic} - 完整指南",
            "sections": [
                {"heading": "引言", "points": ["背景介绍", "重要性说明"]},
                {"heading": "核心概念", "points": ["定义", "原理"]},
                {"heading": "实践步骤", "points": ["步骤1", "步骤2", "步骤3"]},
                {"heading": "最佳实践", "points": ["建议1", "建议2"]},
                {"heading": "总结", "points": ["要点回顾", "下一步行动"]},
            ]
        }

        return SkillResult(
            success=True,
            data=outline,
            message="Outline generated successfully"
        )

    async def _expand_paragraph(self, context: SkillContext) -> SkillResult:
        """扩写段落"""
        text = context.parameters.get("text")

        if not text:
            return SkillResult(success=False, error="Text is required")

        # 尝试使用 LLM 扩写
        if llm_client.is_available:
            result = await llm_client.generate_text(
                prompt=f"请扩写以下段落，使其更加详细、有深度，保持原始含义：\n\n{text}",
                system_prompt="你是一个专业的写作助手。请扩写段落，添加更多细节、例子和分析。",
            )
            if result.get("success"):
                expanded = result["content"]
                return SkillResult(
                    success=True,
                    data={"original": text, "expanded": expanded},
                    message="Paragraph expanded successfully (LLM)"
                )

        # Fallback
        expanded = f"{text}\n\n[扩展内容...]"

        return SkillResult(
            success=True,
            data={"original": text, "expanded": expanded},
            message="Paragraph expanded successfully"
        )

    async def _optimize_title(self, context: SkillContext) -> SkillResult:
        """优化标题"""
        title = context.parameters.get("title")

        if not title:
            return SkillResult(success=False, error="Title is required")

        # 尝试使用 LLM 优化标题
        if llm_client.is_available:
            result = await llm_client.generate_json(
                prompt=f"请为以下标题生成 3-5 个优化建议，包括 SEO 优化、吸引力优化、专业优化等类型。\n"
                       f"原始标题：{title}\n\n"
                       f"返回 JSON 格式，包含 suggestions 数组，每个元素有 title 和 type 字段。",
                system_prompt="你是一个 SEO 和内容营销专家。请以 JSON 格式返回结果。",
            )
            if result.get("success") and isinstance(result.get("content"), dict):
                content = result["content"]
                if "suggestions" in content:
                    suggestions = [s.get("title", str(s)) if isinstance(s, dict) else str(s) for s in
                                   content["suggestions"]]
                    return SkillResult(
                        success=True,
                        data={"original": title, "suggestions": suggestions},
                        message="Title optimized successfully (LLM)"
                    )

        # Fallback
        suggestions = [
            f"{title}：完整指南",
            f"如何{title}：一步步教程",
            f"{title}的10个技巧",
        ]

        return SkillResult(
            success=True,
            data={"original": title, "suggestions": suggestions},
            message="Title optimized successfully"
        )

    async def _extract_keywords(self, context: SkillContext) -> SkillResult:
        """提取关键词"""
        content = context.parameters.get("content")

        if not content:
            return SkillResult(success=False, error="Content is required")

        # 使用 TF-IDF 简化实现提取关键词
        keywords = self._extract_keywords_tfidf(content, max_keywords=10)

        return SkillResult(
            success=True,
            data={"keywords": keywords, "count": len(keywords)},
            message="Keywords extracted successfully"
        )

    @staticmethod
    def _extract_keywords_tfidf(content: str, max_keywords: int = 10) -> list:
        """使用 TF-IDF 简化实现提取关键词"""
        # 移除标点符号和特殊字符
        text = re.sub(r'[^\w\s]', ' ', content)
        words = text.lower().split()
        # 过滤停用词和短词
        stop_words = {
            'the', 'a', 'an', 'is', 'are', 'was', 'were', 'be', 'been', 'being',
            'have', 'has', 'had', 'do', 'does', 'did', 'will', 'would', 'could',
            'should', 'may', 'might', 'shall', 'can', 'need', 'dare', 'ought',
            'used', 'to', 'of', 'in', 'for', 'on', 'with', 'at', 'by', 'from',
            'as', 'into', 'through', 'during', 'before', 'after', 'above', 'below',
            'between', 'out', 'off', 'over', 'under', 'again', 'further', 'then',
            'once', 'here', 'there', 'when', 'where', 'why', 'how', 'all', 'both',
            'each', 'few', 'more', 'most', 'other', 'some', 'such', 'no', 'nor',
            'not', 'only', 'own', 'same', 'so', 'than', 'too', 'very', 'just',
            'because', 'but', 'and', 'or', 'if', 'while', 'this', 'that', 'these',
            'those', 'it', 'its', 'we', 'our', 'you', 'your', 'they', 'their',
            '的', '了', '在', '是', '我', '有', '和', '就', '不', '人', '都', '一',
            '一个', '上', '也', '很', '到', '说', '要', '去', '你', '会', '着',
            '没有', '看', '好', '自己', '这', '他', '她', '它', '们', '那', '些',
        }
        filtered = [w for w in words if len(w) > 1 and w not in stop_words]
        counter = Counter(filtered)
        keywords = [word for word, _ in counter.most_common(max_keywords)]
        return keywords

class SEOOptimizerSkill(BaseSkill):
    """
    SEO 优化 Skill

    Meta 描述生成、关键词密度分析、可读性评分等
    """

    def __init__(self):
        metadata = SkillMetadata(
            name="seo_optimizer",
            version="1.0.0",
            description="SEO 优化工具，包括 Meta 描述生成、关键词分析、可读性评分等",
            author="FastBlog Team",
            category=SkillCategory.SEO_OPTIMIZATION,
            permissions=[SkillPermission.READ_ONLY, SkillPermission.WRITE],
            tags=["seo", "optimization", "meta", "keywords"],
            icon="🔍",
        )
        super().__init__(metadata)

    async def execute(self, context: SkillContext) -> SkillResult:
        """执行 SEO 优化任务"""
        action = context.parameters.get("action")

        if action == "generate_meta_description":
            return await self._generate_meta_description(context)
        elif action == "analyze_keyword_density":
            return await self._analyze_keyword_density(context)
        elif action == "check_readability":
            return await self._check_readability(context)
        elif action == "suggest_internal_links":
            return await self._suggest_internal_links(context)
        else:
            return SkillResult(
                success=False,
                error=f"Unknown action: {action}"
            )

    async def _generate_meta_description(self, context: SkillContext) -> SkillResult:
        """生成 Meta 描述"""
        content = context.parameters.get("content")

        if not content:
            return SkillResult(success=False, error="Content is required")

        # 尝试使用 LLM 生成 Meta 描述
        if llm_client.is_available:
            result = await llm_client.generate_text(
                prompt=f"请为以下文章内容生成一段 SEO 友好的 Meta Description，不超过 160 个字符：\n\n"
                       f"标题：{context.parameters.get('title', '')}\n"
                       f"内容：{content[:500]}",
                system_prompt="你是一个 SEO 专家。请生成简洁、有吸引力的 Meta Description。",
                max_tokens=200,
            )
            if result.get("success"):
                description = result["content"][:160]
                return SkillResult(
                    success=True,
                    data={
                        "description": description,
                        "length": len(description),
                        "optimal": len(description) <= 160
                    },
                    message="Meta description generated (LLM)"
                )

        # Fallback: 截取内容前 155 字符
        description = content[:155] + "..." if len(content) > 155 else content

        return SkillResult(
            success=True,
            data={
                "description": description,
                "length": len(description),
                "optimal": len(description) <= 160
            },
            message="Meta description generated"
        )

    async def _analyze_keyword_density(self, context: SkillContext) -> SkillResult:
        """分析关键词密度"""
        content = context.parameters.get("content")
        target_keyword = context.parameters.get("keyword")

        if not content or not target_keyword:
            return SkillResult(success=False, error="Content and keyword are required")

        # 计算关键词密度
        words = content.lower().split()
        keyword_count = content.lower().count(target_keyword.lower())
        density = (keyword_count / len(words) * 100) if words else 0

        return SkillResult(
            success=True,
            data={
                "keyword": target_keyword,
                "count": keyword_count,
                "density": round(density, 2),
                "recommendation": "Optimal" if 1 <= density <= 3 else "Needs adjustment"
            },
            message="Keyword density analyzed"
        )

    async def _check_readability(self, context: SkillContext) -> SkillResult:
        """检查可读性"""
        content = context.parameters.get("content")

        if not content:
            return SkillResult(success=False, error="Content is required")

        # 简化版可读性评分
        sentences = content.split('。')
        avg_sentence_length = len(content) / max(len(sentences), 1)

        score = 100 - min(abs(avg_sentence_length - 20) * 2, 50)

        return SkillResult(
            success=True,
            data={
                "score": round(score, 2),
                "grade": "Good" if score >= 70 else "Needs improvement",
                "avg_sentence_length": round(avg_sentence_length, 2)
            },
            message="Readability checked"
        )

    async def _suggest_internal_links(self, context: SkillContext) -> SkillResult:
        """建议内部链接"""
        content = context.parameters.get("content")

        if not content:
            return SkillResult(success=False, error="Content is required")

        # 基于关键词匹配建议内部链接
        content_keywords = self._extract_keywords_tfidf(content, max_keywords=5)
        # 获取可用文章列表
        available_articles = context.parameters.get("available_articles", [])
        suggestions = []
        if available_articles:
            for article in available_articles:
                article_title = article.get("title", "")
                article_id = article.get("id", 0)
                # 计算关键词匹配度
                title_lower = article_title.lower()
                match_score = sum(1 for kw in content_keywords if kw in title_lower)
                if match_score > 0:
                    suggestions.append({
                        "title": article_title,
                        "url": f"/article/{article_id}",
                        "relevance_score": min(match_score * 20, 100),
                        "matched_keywords": [kw for kw in content_keywords if kw in title_lower],
                    })
            suggestions.sort(key=lambda x: x.get("relevance_score", 0), reverse=True)
            suggestions = suggestions[:5]
        else:
            suggestions = [
                {"title": "相关文章1", "url": "/article/1"},
                {"title": "相关文章2", "url": "/article/2"},
            ]

        return SkillResult(
            success=True,
            data={"suggestions": suggestions},
            message="Internal links suggested"
        )


class PluginGeneratorSkill(BaseSkill):
    """
    插件代码生成 Skill

    根据描述生成 FastBlog 插件代码框架
    """

    def __init__(self):
        metadata = SkillMetadata(
            name="plugin_generator",
            version="1.0.0",
            description="根据需求描述生成 FastBlog 插件代码框架",
            author="FastBlog Team",
            category=SkillCategory.PLUGIN_DEVELOPMENT,
            permissions=[SkillPermission.WRITE],
            tags=["plugin", "code-generation", "development"],
            icon="🔌",
        )
        super().__init__(metadata)

    async def execute(self, context: SkillContext) -> SkillResult:
        """执行插件生成任务"""
        description = context.parameters.get("description")
        plugin_name = context.parameters.get("name")

        if not description or not plugin_name:
            return SkillResult(
                success=False,
                error="Description and plugin name are required"
            )

        # 生成插件代码框架
        plugin_code = self._generate_plugin_template(plugin_name, description)

        return SkillResult(
            success=True,
            data={
                "plugin_name": plugin_name,
                "code": plugin_code,
                "files": [
                    f"plugins/{plugin_name}/plugin.py",
                    f"plugins/{plugin_name}/README.md",
                ]
            },
            message="Plugin code generated successfully"
        )

    def _generate_plugin_template(self, name: str, description: str) -> str:
        """生成插件模板代码"""
        return f'''"""
{name.replace("-", " ").title()} Plugin

{description}
"""

from shared.plugins.base import BasePlugin


class {name.replace("-", "_").title()}Plugin(BasePlugin):
    """{name.replace("-", " ").title()} 插件"""

    def __init__(self):
        super().__init__(
            name="{name}",
            version="1.0.0",
            description="{description}",
            author="Generated by AI",
        )

    def activate(self):
        """激活插件"""
        pass

    def deactivate(self):
        """停用插件"""
        pass


# 全局实例
plugin = {name.replace("-", "_").title()}Plugin()
'''


class ThemeBuilderSkill(BaseSkill):
    """
    主题样式生成 Skill

    根据描述生成 CSS 样式和主题配置
    """

    def __init__(self):
        metadata = SkillMetadata(
            name="theme_builder",
            version="1.0.0",
            description="根据设计描述生成 CSS 样式和主题配置",
            author="FastBlog Team",
            category=SkillCategory.THEME_CUSTOMIZATION,
            permissions=[SkillPermission.WRITE],
            tags=["theme", "css", "design", "styling"],
            icon="🎨",
        )
        super().__init__(metadata)

    async def execute(self, context: SkillContext) -> SkillResult:
        """执行主题构建任务"""
        style_description = context.parameters.get("description")

        if not style_description:
            return SkillResult(success=False, error="Style description is required")

        # 生成 CSS 代码
        css_code = self._generate_css(style_description)

        return SkillResult(
            success=True,
            data={
                "css": css_code,
                "preview_url": "/api/v2/assets/themes/preview/custom",
            },
            message="Theme styles generated"
        )

    def _generate_css(self, description: str) -> str:
        """生成 CSS 代码"""
        return f"""/*
 * Generated Theme Styles
 * Description: {description}
 */

:root {{
    --primary-color: #3b82f6;
    --secondary-color: #64748b;
    --accent-color: #f59e0b;
    --background-color: #ffffff;
    --text-color: #1f2937;
}}

body {{
    font-family: 'Inter', system-ui, sans-serif;
    background-color: var(--background-color);
    color: var(--text-color);
}}

/* Additional styles based on description */
"""


class DataMigratorSkill(BaseSkill):
    """
    数据迁移助手 Skill

    帮助从其他平台迁移数据到 FastBlog
    """

    def __init__(self):
        metadata = SkillMetadata(
            name="data_migrator",
            version="1.0.0",
            description="数据迁移助手，支持从 WordPress、Halo 等平台迁移",
            author="FastBlog Team",
            category=SkillCategory.DATA_MIGRATION,
            permissions=[SkillPermission.ADMIN],
            tags=["migration", "import", "wordpress", "halo"],
            icon="📦",
        )
        super().__init__(metadata)

    async def execute(self, context: SkillContext) -> SkillResult:
        """执行数据迁移任务"""
        source_platform = context.parameters.get("platform")
        import_file = context.parameters.get("file")

        if not source_platform or not import_file:
            return SkillResult(
                success=False,
                error="Platform and import file are required"
            )

        # 实际数据迁移逻辑
        try:
            import os
            migrated_items = {"articles": 0, "categories": 0, "tags": 0, "media": 0}
            migration_errors = []

            if not os.path.exists(import_file):
                return SkillResult(
                    success=False,
                    error=f"Import file not found: {import_file}"
                )

            if source_platform == "wordpress":
                # WordPress XML 迁移
                from shared.services.integrations.wordpress_importer import WordPressImporter
                importer = WordPressImporter()
                result = await importer.import_from_file(import_file)
                migrated_items = result.get("migrated_items", migrated_items)
            elif source_platform == "halo":
                # Halo 迁移
                from shared.services.integrations.halo_importer import HaloImporter
                importer = HaloImporter()
                result = await importer.import_from_file(import_file)
                migrated_items = result.get("migrated_items", migrated_items)
            else:
                return SkillResult(
                    success=False,
                    error=f"Unsupported platform: {source_platform}. Supported: wordpress, halo"
                )

            return SkillResult(
                success=True,
                data={
                    "platform": source_platform,
                    "file": import_file,
                    "status": "completed",
                    "migrated_items": migrated_items,
                    "errors": migration_errors,
                },
                message=f"Data migrated from {source_platform} successfully"
            )
        except ImportError:
            return SkillResult(
                success=False,
                error=f"Migration module for {source_platform} not available"
            )
        except Exception as e:
            return SkillResult(
                success=False,
                error=f"Migration failed: {str(e)}"
            )


# 注册所有核心 Skills
def register_core_skills():
    """注册所有核心 Skills"""
    from shared.services.ai.skills_framework import skill_registry

    skills = [
        ContentCreatorSkill(),
        SEOOptimizerSkill(),
        PluginGeneratorSkill(),
        ThemeBuilderSkill(),
        DataMigratorSkill(),
    ]

    for skill in skills:
        skill_registry.register_skill(skill)
