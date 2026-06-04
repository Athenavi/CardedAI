"""
搜索相关的工具函数
"""
import os
import re
import time
from xml.etree import ElementTree as ET

from fastapi import Request
from sqlalchemy import select

from shared.models import ArticleContent
from shared.models.article import Article
from shared.models.search_history import SearchHistory
from src.utils.database.unified_manager import db_manager


async def save_search_history(user_id, keyword, results_count):
    """保存搜索历史"""
    async with db_manager.get_session() as session:
        new_search_history = SearchHistory(user_id=user_id, keyword=keyword, results_count=results_count)
        session.add(new_search_history)
        await session.commit()


async def get_user_search_history(user_id):
    async with db_manager.get_session() as session:
        result = await session.execute(
            select(SearchHistory.keyword)
            .where(SearchHistory.user_id == user_id)
            .order_by(SearchHistory.created_at.desc())
        )
        history_keywords = result.all()
        # 使用集合去重
        unique_keywords = set(keyword[0] for keyword in history_keywords)
        # 将集合转换为列表
        return list(unique_keywords)


async def search_handler(request: Request, user_id, domain, global_encoding, max_cache_timestamp):
    matched_content = []

    def strip_html_tags(text):
        """去除HTML标签"""
        if text is None:
            return ''
        return re.sub('<[^<]+?>', '', text)

    if request.method == 'POST':
        # FastAPI中通常通过依赖注入验证CSRF，这里暂时跳过CSRF验证
        # 实际应用中应使用FastAPI的依赖注入机制来处理CSRF保护
        async with db_manager.get_session() as db_session:
            form_data = await request.form()
            keyword = form_data.get('keyword')  # 获取搜索关键词
            # 对关键词进行转义，替换特殊字符
            safe_keyword = re.sub(r'[\\/*?:"<>|]', '', keyword)
            cache_dir = os.path.join('temp', 'search')
            os.makedirs(cache_dir, exist_ok=True)
            cache_path = os.path.join(cache_dir, safe_keyword + '.xml')

            # 检查缓存是否失效
            if os.path.isfile(cache_path) and (
                    time.time() - os.path.getmtime(cache_path) < max_cache_timestamp):
                # 读取缓存并继续处理
                with open(cache_path, 'r', encoding=global_encoding) as cache_file:
                    match_data = cache_file.read()
            else:
                # 查询公开的文章（只索引已发布、非隐藏的文章）
                result = await db_session.execute(
                    select(Article, ArticleContent)
                    .join(ArticleContent, Article.id == ArticleContent.aid)
                    .where(Article.status == 1, Article.hidden == False)
                )
                articles = result.all()

                # 创建XML根元素
                root = ET.Element('rss')
                root.set('version', '2.0')

                # 为每个匹配的文章创建XML条目
                for article, content in articles:
                    # 检查文章是否包含关键词（在标题或内容中）
                    if (keyword.lower() in article.title.lower() or
                            keyword.lower() in strip_html_tags(content.content).lower()):
                        item = ET.SubElement(root, 'item')

                        title_elem = ET.SubElement(item, 'title')
                        title_elem.text = article.title

                        link_elem = ET.SubElement(item, 'link')
                        link_elem.text = f"{domain}p/{article.slug}"

                        pub_date_elem = ET.SubElement(item, 'pubDate')
                        pub_date_elem.text = article.created_at.strftime('%a, %d %b %Y %H:%M:%S GMT')

                        description_elem = ET.SubElement(item, 'description')
                        desc_text = article.excerpt if article.excerpt else strip_html_tags(content.content)[
                                                                                :200] + '...'
                        description_elem.text = desc_text

                # 创建XML树并写入缓存
                tree = ET.ElementTree(root)
                match_data = ET.tostring(tree.getroot(), encoding="unicode", method='xml')

                with open(cache_path, 'w', encoding=global_encoding) as cache_file:
                    cache_file.write(match_data)

        # 解析XML数据
        parsed_data = ET.fromstring(match_data)
        for item in parsed_data.findall('item'):
            content = {
                'title': item.find('title').text,
                'link': item.find('link').text,
                'pubDate': item.find('pubDate').text,
                'description': item.find('description').text
            }
            matched_content.append(content)
            if item:
                await save_search_history(user_id, keyword, len(matched_content) or 0)

    history_list = await get_user_search_history(user_id)
    # 在FastAPI中，CSRF保护通常通过其他方式实现
    return {"request": request,
            'historyList': history_list,
            'results': matched_content}
