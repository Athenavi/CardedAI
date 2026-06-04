"""
标签建议 API
提供标签自动补全功能
"""


from fastapi import APIRouter, Query

from shared.models.article import Article
from src.extensions import cache, get_async_db_session as get_async_db
from src.utils.filters import f2list

from src.unified_logger import default_logger as logger

router = APIRouter(tags=["tags"])


@router.get('/suggest')
async def suggest_tags(query: str = Query("", alias="q")):
    """
    根据前缀建议标签
    
    Args:
        query: 标签前缀
        
    Returns:
        匹配的标签列表（最多5个）
    """
    # 使用带保护的缓存来存储去重后的标签列表
    cache_key = 'unique_tags'
    unique_tags = cache.get_with_stale_data(
        cache_key,
        lambda: _generate_unique_tags(),
        fresh_timeout=600,  # 10分钟新鲜时间
        stale_timeout=1800  # 30分钟陈旧时间
    )

    # 过滤出匹配前缀的标签
    matched_tags = [tag for tag in unique_tags if tag.startswith(query)]

    # 返回前五个匹配的标签
    return matched_tags[:5]


async def _generate_unique_tags():
    """生成唯一的标签列表"""
    logger.info("缓存未命中，从数据库加载标签...")
    db_session = await get_async_db()

    # 获取所有文章的标签字符串
    tags_results = db_session.query(Article.tags_list).all()

    # 处理标签数据
    all_tags = []
    for tag_string in tags_results:
        if tag_string and tag_string[0]:  # 确保不是空字符串  
            all_tags.extend(f2list(tag_string[0].strip()))

    # 去重并排序
    unique_tags = sorted(set(all_tags))
    logger.info(f"加载并处理完成，唯一标签数量: {len(unique_tags)}")
    return unique_tags
