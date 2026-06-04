"""
OpenAPI 文档增强模块
为 API 端点提供详细的请求/响应示例，使文档更加 AI-Friendly
"""

# 文章相关示例
ARTICLE_LIST_EXAMPLE = {
    "summary": "获取文章列表",
    "description": """
获取分页的文章列表，支持多种筛选和搜索功能。

**功能特性**:
- 分页支持 (page, per_page)
- 关键词搜索 (search) - 搜索标题和摘要
- 分类筛选 (category_id)
- 作者筛选 (user_id)
- 状态筛选 (status: draft/published/deleted)

**使用场景**:
- 首页文章展示
- 分类页面文章列表
- 用户个人文章列表
- 管理后台文章管理
    """,
    "parameters": {
        "page": {"example": 1, "description": "页码，从1开始"},
        "per_page": {"example": 10, "description": "每页数量，范围1-100"},
        "search": {"example": "Python教程", "description": "搜索关键词"},
        "category_id": {"example": 5, "description": "分类ID"},
        "user_id": {"example": 3, "description": "用户ID"},
        "status": {"example": "published", "description": "文章状态"}
    },
    "response_example": {
        "success": True,
        "data": [
            {
                "id": 1,
                "title": "FastAPI 入门教程",
                "slug": "fastapi-intro",
                "excerpt": "本文介绍 FastAPI 的基本用法...",
                "cover_image": "/media/covers/fastapi.jpg",
                "tags": ["Python", "FastAPI", "后端"],
                "author": {
                    "id": 1,
                    "username": "admin"
                },
                "category_id": 1,
                "category_name": "技术教程",
                "views": 1234,
                "likes": 56,
                "status": 1,
                "created_at": "2026-04-01T10:00:00",
                "updated_at": "2026-04-09T15:30:00"
            }
        ],
        "pagination": {
            "current_page": 1,
            "per_page": 10,
            "total": 100,
            "total_pages": 10,
            "has_next": True,
            "has_prev": False
        }
    }
}

ARTICLE_DETAIL_EXAMPLE = {
    "summary": "获取文章详情",
    "description": """
获取指定文章的详细信息，包括完整内容和元数据。

**注意**:
- 访问此接口会自动增加文章浏览量
- 返回的内容是 HTML 格式（Markdown 已转换）
- 如需原始 Markdown，请使用 `/articles/{id}/raw` 接口
    """,
    "response_example": {
        "success": True,
        "data": {
            "id": 1,
            "title": "FastAPI 入门教程",
            "slug": "fastapi-intro",
            "excerpt": "本文介绍 FastAPI 的基本用法...",
            "content": "<h1>FastAPI 入门</h1><p>FastAPI 是一个现代...</p>",
            "author": {
                "id": 1,
                "username": "admin",
                "bio": "全栈开发者",
                "profile_picture": "/api/v2/static/avatar/admin.webp"
            },
            "category_id": 1,
            "views": 1235,
            "likes": 56,
            "status": 1,
            "created_at": "2026-04-01T10:00:00",
            "updated_at": "2026-04-09T15:30:00"
        }
    }
}

ARTICLE_CREATE_EXAMPLE = {
    "summary": "创建新文章",
    "description": """
创建一篇新文章，需要认证权限。

**权限要求**:
- 需要登录
- 用户角色至少为 Contributor

**内容格式**:
- content 字段支持 Markdown 格式
- tags 是字符串数组
- cover_image 是媒体文件路径
    """,
    "request_example": {
        "title": "我的第一篇文章",
        "slug": "my-first-article",
        "excerpt": "这是文章的简短描述...",
        "content": "# 标题\n\n这是文章内容，支持 **Markdown** 语法。",
        "category_id": 1,
        "tags": ["Python", "教程"],
        "cover_image": "/media/covers/example.jpg",
        "status": "draft"
    },
    "response_example": {
        "success": True,
        "data": {
            "id": 101,
            "title": "我的第一篇文章",
            "message": "文章创建成功"
        }
    }
}

# 用户认证示例
AUTH_LOGIN_EXAMPLE = {
    "summary": "用户登录",
    "description": """
使用用户名/邮箱和密码进行登录，获取 JWT Token。

**认证方式**:
1. 使用此接口获取 access_token
2. 在后续请求的 Header 中添加: `Authorization: Bearer <token>`

**Token 有效期**: 1小时 (3600秒)
    """,
    "request_example": {
        "username": "admin@example.com",
        "password": "your_password"
    },
    "response_example": {
        "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
        "token_type": "bearer",
        "user": {
            "id": 1,
            "username": "admin",
            "email": "admin@example.com",
            "role": "administrator"
        }
    }
}

# 媒体上传示例
MEDIA_UPLOAD_EXAMPLE = {
    "summary": "上传媒体文件",
    "description": """
上传图片、视频等媒体文件。

**支持的文件类型**:
- 图片: jpg, jpeg, png, gif, webp
- 视频: mp4, avi, mov
- 文档: pdf, doc, docx

**文件大小限制**: 10MB

**使用方式**:
使用 multipart/form-data 格式上传
    """,
    "request_example": {
        "file": "(binary file data)",
        "folder": "articles/2026/04"
    },
    "response_example": {
        "success": True,
        "data": {
            "id": 42,
            "filename": "image_20260409_123456.jpg",
            "url": "/media/uploads/image_20260409_123456.jpg",
            "thumbnail_url": "/media/thumbnails/image_20260409_123456_thumb.jpg",
            "size": 1024000,
            "mime_type": "image/jpeg"
        }
    }
}

# 分类管理示例
CATEGORY_LIST_EXAMPLE = {
    "summary": "获取分类列表",
    "description": "获取所有文章分类，支持层级结构",
    "response_example": {
        "success": True,
        "data": [
            {
                "id": 1,
                "name": "技术教程",
                "slug": "tech-tutorials",
                "description": "编程和技术相关教程",
                "parent_id": None,
                "article_count": 45,
                "order": 1
            },
            {
                "id": 2,
                "name": "Python",
                "slug": "python",
                "description": "Python 相关内容",
                "parent_id": 1,
                "article_count": 23,
                "order": 1
            }
        ]
    }
}

# 仪表板统计示例
DASHBOARD_STATS_EXAMPLE = {
    "summary": "获取仪表板统计数据",
    "description": "获取博客系统的各项统计数据，用于管理后台仪表板展示",
    "response_example": {
        "success": True,
        "data": {
            "total_articles": 150,
            "published_articles": 120,
            "draft_articles": 30,
            "total_users": 500,
            "active_users": 450,
            "total_views": 125000,
            "total_likes": 8500,
            "total_comments": 3200,
            "recent_articles": [
                {
                    "id": 150,
                    "title": "最新文章标题",
                    "views": 234,
                    "created_at": "2026-04-09T10:00:00"
                }
            ],
            "popular_articles": [
                {
                    "id": 1,
                    "title": "热门文章标题",
                    "views": 5678,
                    "likes": 234
                }
            ],
            "views_trend": [
                {"date": "2026-04-01", "views": 1200},
                {"date": "2026-04-02", "views": 1350}
            ]
        }
    }
}

# 插件管理示例
PLUGIN_LIST_EXAMPLE = {
    "summary": "获取插件列表",
    "description": "获取所有已安装的插件及其状态信息",
    "response_example": {
        "success": True,
        "data": [
            {
                "id": 1,
                "name": "SEO Optimizer",
                "slug": "seo-optimizer",
                "version": "1.0.0",
                "description": "自动优化文章 SEO",
                "author": "FastBlog Team",
                "active": True,
                "installed": True,
                "settings": {
                    "auto_generate_meta": True,
                    "keyword_density": 2.5
                }
            }
        ]
    }
}

# 通用错误响应示例
ERROR_RESPONSE_EXAMPLE = {
    "400": {
        "description": "请求参数错误",
        "content": {
            "application/json": {
                "example": {
                    "success": False,
                    "error": "Invalid parameter: page must be greater than 0"
                }
            }
        }
    },
    "401": {
        "description": "未授权访问",
        "content": {
            "application/json": {
                "example": {
                    "success": False,
                    "error": "Authentication required"
                }
            }
        }
    },
    "403": {
        "description": "权限不足",
        "content": {
            "application/json": {
                "example": {
                    "success": False,
                    "error": "Insufficient permissions"
                }
            }
        }
    },
    "404": {
        "description": "资源不存在",
        "content": {
            "application/json": {
                "example": {
                    "success": False,
                    "error": "Article not found"
                }
            }
        }
    },
    "500": {
        "description": "服务器内部错误",
        "content": {
            "application/json": {
                "example": {
                    "success": False,
                    "error": "Internal server error"
                }
            }
        }
    }
}

# AI Agent 使用指南
AI_AGENT_GUIDE = """
# AI Agent 调用指南

本 API 设计遵循 RESTful 原则，适合 AI Agent 自动调用。

## 调用流程示例

### 1. 发布一篇新文章

```python
# Step 1: 登录获取 token
POST /api/v1/auth/login
{
    "username": "admin@example.com",
    "password": "password123"
}

# Step 2: 使用 token 创建文章
POST /api/v1/articles
Headers: {
    "Authorization": "Bearer <access_token>",
    "Content-Type": "application/json"
}
Body: {
    "title": "AI 生成的文章",
    "content": "# 标题\\n\\n这是文章内容...",
    "category_id": 1,
    "tags": ["AI", "自动化"],
    "status": "published"
}
```

### 2. 查询并更新文章

```python
# Step 1: 搜索文章
GET /api/v1/articles?search=AI&page=1&per_page=10

# Step 2: 获取文章详情
GET /api/v1/articles/{article_id}

# Step 3: 更新文章
PUT /api/v1/articles/{article_id}
{
    "title": "更新后的标题",
    "content": "更新后的内容..."
}
```

### 3. 上传封面图片

```python
POST /api/v1/media/upload
Headers: {
    "Authorization": "Bearer <access_token>"
}
Form Data: {
    "file": <binary_data>,
    "folder": "covers"
}
```

## 最佳实践

1. **错误处理**: 始终检查响应的 `success` 字段
2. **分页**: 对于列表接口，合理使用分页参数
3. **缓存**: 对不常变化的数据（如分类列表）进行缓存
4. **批量操作**: 优先使用批量接口减少请求次数
5. **重试机制**: 对于网络错误实现指数退避重试

## 常见场景

### 内容管理系统 (CMS)
- 文章 CRUD: `/api/v1/articles`
- 分类管理: `/api/v1/categories`
- 媒体管理: `/api/v1/media`

### 用户管理
- 用户列表: `/api/v1/users`
- 角色分配: `/api/v1/roles`
- 权限控制: `/api/v1/permissions`

### 数据分析
- 统计数据: `/api/v1/dashboard/stats`
- 访问趋势: `/api/v1/dashboard/analytics`
- 热门内容: `/api/v1/dashboard/popular`

### 系统管理
- 插件管理: `/api/v1/plugins`
- 主题管理: `/api/v1/themes`
- 系统设置: `/api/v1/settings`
"""
