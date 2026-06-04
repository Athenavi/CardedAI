# FastBlog Python SDK

FastBlog API V2 的官方 Python SDK，提供同步和异步客户端。

> **API 版本**: V2 (`/api/v2/`)  
> **FastBlog 版本**: V0.3.26.0521+  
> **Python 要求**: 3.10+

## 安装

```bash
pip install fastblog-sdk
```

或者从源码安装：

```bash
cd sdk/python
pip install -e .
```

### 依赖

- **同步客户端**: `requests`
- **异步客户端**: `aiohttp` (可选)

安装所有依赖：

```bash
pip install requests aiohttp
```

## 快速开始

### 同步客户端

```python
from fastblog_sdk import FastBlogClient

# 创建客户端（默认使用 V2 API）
client = FastBlogClient("http://localhost:9421/api/v2")

# 登录（支持用户名或邮箱）
client.login("admin@example.com", "password")

# 获取文章列表
articles = client.get_articles(page=1, per_page=10)
print(f"找到 {len(articles['data'])} 篇文章")

# 创建文章
new_article = client.create_article({
    "title": "我的文章",
    "content": "# Hello World",
    "status": 0  # 草稿
})

# 登出
client.logout()
```

### 异步客户端

```python
import asyncio
from fastblog_sdk import AsyncFastBlogClient

async def main():
    # 创建客户端（默认使用 V2 API）
    async with AsyncFastBlogClient("http://localhost:9421/api/v2") as client:
        
        # 登录（支持用户名或邮箱）
        await client.login("admin@example.com", "password")
        
        # 获取文章
        articles = await client.get_articles(page=1, per_page=10)
        print(f"找到 {len(articles['data'])} 篇文章")
        
        # 创建文章
        new_article = await client.create_article({
            "title": "我的文章",
            "content": "# Hello World",
            "status": 0
        })

asyncio.run(main())
```

## 完整示例

查看 `examples/` 目录中的完整示例：

- `basic_usage.py` - 基本用法示例
- `complete_example.py` - 完整功能示例（同步）
- `async_example.py` - 异步客户端示例

运行示例：

```bash
# 同步示例
python examples/complete_example.py

# 异步示例
python examples/async_example.py
```

## API 参考

### 认证相关 (`/api/v2/auth/`)

| 方法                                    | 说明                                                 |
|---------------------------------------|----------------------------------------------------|
| `login(username, password)`           | 用户登录（支持用户名或邮箱），返回 `access_token` 和 `refresh_token` |
| `logout()`                            | 用户登出，将当前 token 加入黑名单                               |
| `register(email, password, username)` | 用户注册                                               |

### 文章相关 (`/api/v2/articles/`)

| 方法                                       | 说明     |
|------------------------------------------|--------|
| `get_articles(page, per_page, **params)` | 获取文章列表 |
| `get_article(article_id)`                | 获取单篇文章 |
| `create_article(data)`                   | 创建文章   |
| `update_article(article_id, data)`       | 更新文章   |
| `delete_article(article_id)`             | 删除文章   |

### 分类相关 (`/api/v2/categories/`)

| 方法                                         | 说明     |
|--------------------------------------------|--------|
| `get_categories()`                         | 获取分类列表 |
| `create_category(name, slug, description)` | 创建分类   |

### 用户相关 (`/api/v2/users/`)

| 方法                     | 说明                    |
|------------------------|-----------------------|
| `get_current_user()`   | 获取当前用户信息（`/users/me`） |
| `update_profile(data)` | 更新用户资料（`/users/me`）   |

### 媒体相关 (`/api/v2/media/`)

| 方法                        | 说明     |
|---------------------------|--------|
| `upload_media(file_path)` | 上传媒体文件 |

### 仪表板相关 (`/api/v2/dashboard/`)

| 方法                              | 说明        |
|---------------------------------|-----------|
| `get_dashboard_stats()`         | 获取仪表板统计数据 |
| `get_dashboard_analytics(days)` | 获取仪表板分析数据 |

### SEO 追踪相关 (`/api/v2/seo/tracking/`)

| 方法                              | 说明             |
|---------------------------------|----------------|
| `get_seo_traffic(days)`         | 获取 SEO 流量数据    |
| `get_top_keywords(limit, days)` | 获取热门关键词        |
| `get_seo_dashboard()`           | 获取 SEO 仪表板概览数据 |

## 功能特性

- ✅ 完整覆盖 V2 API（28+ 端点）
- ✅ 同步和异步客户端
- ✅ 自动 JWT Token 管理（access_token / refresh_token）
- ✅ 类型提示支持
- ✅ 详细的文档字符串
- ✅ 错误处理
- ✅ 上下文管理器支持
- ✅ 会话自动管理

## 错误处理

```python
from fastblog_sdk import FastBlogClient
import requests

client = FastBlogClient("http://localhost:9421/api/v2")

try:
    articles = client.get_articles()
except requests.exceptions.HTTPError as e:
    print(f"HTTP 错误: {e}")
except requests.exceptions.ConnectionError:
    print("连接错误：无法连接到服务器")
except requests.exceptions.Timeout:
    print("请求超时")
except Exception as e:
    print(f"未知错误: {e}")
```

## 最佳实践

### 1. 使用上下文管理器

```python
# 推荐：自动管理会话
with FastBlogClient("http://localhost:9421/api/v2") as client:
    client.login("admin@example.com", "password")
    # ... 执行操作
# 会话自动关闭
```

### 2. 批量操作

```python
# 异步客户端适合批量操作
async def batch_create_articles():
    async with AsyncFastBlogClient("http://localhost:9421/api/v2") as client:
        await client.login("admin@example.com", "password")
        
        tasks = []
        for i in range(10):
            task = client.create_article({
                'title': f'Article {i}',
                'content': f'Content {i}'
            })
            tasks.append(task)
        
        results = await asyncio.gather(*tasks)
        return results
```

### 3. 错误重试

```python
import time
from fastblog_sdk import FastBlogClient

def request_with_retry(client, func, *args, max_retries=3, **kwargs):
    for attempt in range(max_retries):
        try:
            return func(*args, **kwargs)
        except Exception as e:
            if attempt == max_retries - 1:
                raise
            print(f"Attempt {attempt + 1} failed: {e}")
            time.sleep(2 ** attempt)  # 指数退避

# 使用
articles = request_with_retry(client, client.get_articles, page=1)
```

## API 参考文档

完整 API 文档请访问：https://github.com/fastblog/fast_blog/docs

## 开发

### 运行测试

```bash
# 安装测试依赖
pip install pytest pytest-asyncio

# 运行测试
pytest tests/
```

### 代码风格

本项目遵循 PEP 8 规范，使用 black 进行格式化：

```bash
pip install black
black fastblog_sdk/
```

## License

MIT License
