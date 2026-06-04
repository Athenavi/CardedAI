"""
多语言 Hreflang 标签服务
自动为文章页面生成 hreflang HTML 标签
"""
from typing import Dict, Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from shared.models.article_i18n import ArticleI18n
from shared.services.seo.hreflang_generator import hreflang_generator


class MultilingualHreflangService:
    """
    多语言 Hreflang 标签服务
    
    功能:
    1. 根据文章ID查询所有语言版本
    2. 生成 hreflang HTML 标签
    3. 集成到页面 meta 标签中
    """

    def __init__(self, base_url: str = "http://localhost:8000"):
        self.base_url = base_url.rstrip('/')

    async def get_article_translations(
            self,
            db: AsyncSession,
            article_id: int
    ) -> Dict[str, Dict]:
        """
        获取文章的所有翻译版本
        
        Args:
            db: 数据库会话
            article_id: 文章ID
            
        Returns:
            翻译字典 {language_code: {slug, title, url}}
        """
        stmt = select(ArticleI18n).where(ArticleI18n.article == article_id)
        result = await db.execute(stmt)
        translations = result.scalars().all()

        translation_dict = {}
        for trans in translations:
            # 构建翻译版本的URL
            if trans.slug:
                url = f"{self.base_url}/{trans.language_id}/blog/p/{trans.slug}"
            else:
                url = f"{self.base_url}/{trans.language_id}/blog/{article_id}.html"

            translation_dict[trans.language_id] = {
                'slug': trans.slug,
                'title': trans.title,
                'url': url,
                'excerpt': trans.excerpt
            }

        return translation_dict

    async def generate_hreflang_for_article(
            self,
            db: AsyncSession,
            article_id: int,
            current_language: str = "en",
            include_x_default: bool = True
    ) -> str:
        """
        为文章生成 hreflang HTML 标签
        
        Args:
            db: 数据库会话
            article_id: 文章ID
            current_language: 当前语言
            include_x_default: 是否包含 x-default
            
        Returns:
            hreflang HTML 字符串
        """
        # 获取所有翻译
        translations = await self.get_article_translations(db, article_id)

        if not translations:
            return ""

        # 构建当前文章的URL（假设当前是主语言版本）
        from shared.models.article import Article
        stmt = select(Article).where(Article.id == article_id)
        result = await db.execute(stmt)
        article = result.scalar_one_or_none()

        if not article:
            return ""

        # 构建当前URL
        if article.slug:
            current_url = f"{self.base_url}/blog/p/{article.slug}"
        else:
            current_url = f"{self.base_url}/blog/{article.id}.html"

        # 构建翻译URL映射
        translation_urls = {
            lang: data['url']
            for lang, data in translations.items()
        }

        # 使用 hreflang 生成器
        tags = hreflang_generator.generate_hreflang_tags(
            current_url=current_url,
            translations=translation_urls,
            default_language=current_language,
            include_x_default=include_x_default
        )

        # 渲染为HTML
        html = hreflang_generator.render_html_tags(tags)

        return html

    async def inject_hreflang_to_meta(
            self,
            db: AsyncSession,
            meta_data: Dict,
            article_id: Optional[int] = None,
            current_language: str = "en"
    ) -> Dict:
        """
        将 hreflang 标签注入到页面 meta 数据中
        
        Args:
            db: 数据库会话
            meta_data: 现有的 meta 数据
            article_id: 文章ID（可选）
            current_language: 当前语言
            
        Returns:
            更新后的 meta 数据
        """
        if not article_id:
            return meta_data

        # 生成 hreflang 标签
        hreflang_html = await self.generate_hreflang_for_article(
            db=db,
            article_id=article_id,
            current_language=current_language
        )

        if hreflang_html:
            # 将 hreflang 标签添加到 meta 数据中
            if 'custom_head' not in meta_data:
                meta_data['custom_head'] = ''

            meta_data['custom_head'] += '\n' + hreflang_html

        return meta_data


# 全局实例
multilingual_hreflang_service = MultilingualHreflangService()
