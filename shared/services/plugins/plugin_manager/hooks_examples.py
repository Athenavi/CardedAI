"""
插件钩子集成示例
展示如何在现有代码中集成插件系统

使用方法:
1. 在适当的位置导入 trigger_plugin_event 或 apply_plugin_filter
2. 调用相应的函数触发插件钩子
3. 插件会自动响应这些事件
"""
from shared.services.plugins.plugin_manager.init import trigger_plugin_event, apply_plugin_filter


# ============ 示例1: 在文章发布时触发事件 ============
async def example_article_publish(article_data: dict):
    """
    文章发布示例
    
    在文章成功发布后调用此函数
    """

    # 触发文章发布事件
    await trigger_plugin_event('article_published', {
        'id': article_data.get('id'),
        'title': article_data.get('title'),
        'slug': article_data.get('slug'),
        'content': article_data.get('content'),
        'excerpt': article_data.get('excerpt'),
        'tags': article_data.get('tags', []),
        'category_id': article_data.get('category_id'),
        'user_id': article_data.get('user_id'),
        'status': 'published',
        'created_at': article_data.get('created_at'),
    })

    print("Article published and plugins notified")


# ============ 示例2: 在文章更新时触发事件 ============
async def example_article_update(article_data: dict, updated_fields: list):
    """
    文章更新示例
    
    在文章更新后调用
    """

    await trigger_plugin_event('article_updated', {
        'id': article_data.get('id'),
        'title': article_data.get('title'),
        'updated_fields': updated_fields,  # ['title', 'content', etc.]
        'updated_at': article_data.get('updated_at'),
    })


# ============ 示例3: 在文章删除时触发事件 ============
async def example_article_delete(article_id: int, article_data: dict):
    """
    文章删除示例
    """

    await trigger_plugin_event('article_deleted', {
        'id': article_id,
        'title': article_data.get('title'),
        'deleted_at': article_data.get('deleted_at'),
    })


# ============ 示例4: 在用户注册时触发事件 ============
async def example_user_registered(user_data: dict):
    """
    用户注册示例
    """

    await trigger_plugin_event('user_registered', {
        'user_id': user_data.get('id'),
        'username': user_data.get('username'),
        'email': user_data.get('email'),
        'registered_at': user_data.get('created_at'),
    })


# ============ 示例5: 在登录尝试时触发事件 ============
async def example_login_attempt(ip: str, username: str, success: bool):
    """
    登录尝试示例
    """

    await trigger_plugin_event('login_attempt', {
        'ip': ip,
        'username': username,
        'success': success,
        'timestamp': __import__('datetime').datetime.now().isoformat(),
    })


# ============ 示例6: 使用过滤器增强搜索结果 ============
def example_enhance_search(original_results: dict, query: str) -> dict:
    """
    增强搜索结果示例
    
    在返回搜索结果前调用,让插件可以增强结果
    """

    # 应用搜索过滤器
    enhanced_results = apply_plugin_filter('search_results', original_results, query=query)

    return enhanced_results


# ============ 示例7: 使用过滤器处理页面元标签 ============
def example_generate_meta_tags(page_type: str, page_data: dict) -> list:
    """
    生成页面元标签示例
    
    在渲染页面前调用,让SEO插件可以添加元标签
    """

    meta_data = {
        'page_type': page_type,
        'data': page_data,
        'tags': [],  # 初始为空列表
    }

    # 根据页面类型应用不同的过滤器
    if page_type == 'article':
        enhanced_meta = apply_plugin_filter('page_meta_tags', meta_data)
    elif page_type == 'homepage':
        enhanced_meta = apply_plugin_filter('homepage_meta_tags', meta_data)
    else:
        enhanced_meta = meta_data

    return enhanced_meta.get('tags', [])


# ============ 示例8: 在内容输出前清理XSS ============
def example_sanitize_output(content: str) -> str:
    """
    清理输出内容示例
    
    在输出用户生成的内容前调用
    """

    # 应用输出过滤器(安全插件会清理XSS)
    clean_content = apply_plugin_filter('output_content', content)

    return clean_content


# ============ 示例9: 追踪页面访问 ============
async def example_track_page_view(request_data: dict):
    """
    页面访问追踪示例
    
    在每个页面请求时调用
    """

    await trigger_plugin_event('page_view', {
        'url': request_data.get('url'),
        'title': request_data.get('title'),
        'user_id': request_data.get('user_id'),
        'ip': request_data.get('ip'),
        'referrer': request_data.get('referrer'),
        'user_agent': request_data.get('user_agent'),
        'timestamp': __import__('datetime').datetime.now().isoformat(),
    })


# ============ 示例10: 在媒体上传时触发事件 ============
async def example_media_uploaded(media_data: dict):
    """
    媒体上传示例
    """

    await trigger_plugin_event('media_uploaded', {
        'media_id': media_data.get('id'),
        'filename': media_data.get('filename'),
        'file_type': media_data.get('file_type'),
        'file_size': media_data.get('file_size'),
        'url': media_data.get('url'),
        'uploaded_by': media_data.get('user_id'),
    })


# ============ 实际集成到articles.py的示例 ============
"""
在 src/api/v1/articles.py 中集成:

1. 在文章创建/发布成功后:

```python


@router.post("/articles", ...)
async def create_article(...):
    # ... 创建文章逻辑 ...
    
    # 文章创建成功后触发事件
    await trigger_plugin_event('article_published', {
        'id': article.id,
        'title': article.title,
        'slug': article.slug,
        'content': content,
        'excerpt': article.excerpt,
        'tags': article.tags_list or [],
        'category_id': article.category,
        'user_id': article.user,
        'status': 'published',
        'created_at': article.created_at,
    })
    
    return ApiResponse(success=True, data=article_data)
```

2. 在获取文章详情时增加浏览量追踪:

```python
@router.get("/{article_id}", ...)
async def get_article_detail_api(...):
    # ... 获取文章逻辑 ...
    
    # 追踪页面访问
    
    await trigger_plugin_event('page_view', {
        'url': f'/p/{article.slug}',
        'title': article.title,
        'user_id': current_user_id if current_user else None,
        'ip': request.client.host,
        'referrer': request.headers.get('referer'),
        'user_agent': request.headers.get('user-agent'),
    })
    
    return ApiResponse(success=True, data=article_data)
```

3. 在搜索API中增强结果:

```python
@router.get("/search", ...)
async def search_articles(...):
    # ... 基础搜索逻辑 ...
    
    # 让插件增强搜索结果
    
    search_results = apply_plugin_filter('search_results', results, query=search_query)
    
    return ApiResponse(success=True, data=search_results)
```
"""

# ============ 可用的钩子事件列表 ============
"""
Actions (动作 - 无返回值):
- article_published      # 文章发布
- article_updated        # 文章更新  
- article_deleted        # 文章删除
- user_registered        # 用户注册
- login_attempt          # 登录尝试
- page_view              # 页面访问
- media_uploaded         # 媒体上传
- comment_created        # 评论创建
- sitemap_generation     # Sitemap生成

Filters (过滤器 - 有返回值):
- search_results         # 搜索结果增强
- page_meta_tags         # 页面元标签
- homepage_meta_tags     # 首页元标签
- output_content         # 输出内容清理(XSS)
- media_url             # 媒体URL重写(CDN)
- before_request         # 请求前检查(安全)
- article_content_footer # 文章内容底部(分享按钮)
"""

# ============ 最佳实践 ============
"""
1. 错误处理:
   - 插件钩子调用应该包裹在try-except中
   - 插件失败不应影响主功能
   
2. 性能考虑:
   - 异步事件使用 await trigger_plugin_event()
   - 同步过滤器使用 apply_plugin_filter()
   - 避免在热点路径上执行重型操作
   
3. 数据格式:
   - 传递完整的数据对象
   - 使用标准的字段名
   - 包含足够的上下文信息
   
4. 文档化:
   - 在调用位置注释说明触发的钩子
   - 列出可能响应的插件
   - 说明预期的行为
"""
