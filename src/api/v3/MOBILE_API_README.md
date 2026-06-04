# FastBlog 移动端 API (v3)

**适用版本**: FastBlog V0.3.26.0521+

## 概述

FastBlog v3 API 是专门为移动端App设计的RESTful API接口，提供优化的数据传输和简化的响应结构。

## 基础URL

```
http://your-domain.com/api/v3
```

## 认证

大多数API端点需要JWT token认证。在请求头中添加：

```
Authorization: Bearer <your_jwt_token>
```

## API端点

### 认证模块 (`/api/v3/auth`)

#### 登录

```
POST /api/v3/auth/login
Content-Type: application/json

{
  "username": "user@example.com",  // 用户名或邮箱
  "password": "your_password"
}

Response:
{
  "success": true,
  "data": {
    "user": {
      "id": 1,
      "username": "john",
      "email": "john@example.com",
      "avatar": "avatar.jpg",
      "vip_level": 0
    },
    "access_token": "eyJ...",
    "refresh_token": "eyJ...",
    "message": "登录成功"
  }
}
```

#### 注册

```
POST /api/v3/auth/register
Content-Type: application/json

{
  "username": "newuser",
  "email": "newuser@example.com",
  "password": "secure_password"
}

Response:
{
  "success": true,
  "data": {
    "user": {...},
    "access_token": "eyJ...",
    "refresh_token": "eyJ...",
    "message": "注册成功"
  }
}
```

### 文章模块 (`/api/v3/articles`)

#### 获取文章列表

```
GET /api/v3/articles/list?page=1&per_page=20&category_id=1&search=keyword

Response:
{
  "success": true,
  "data": {
    "articles": [
      {
        "id": 1,
        "title": "Article Title",
        "excerpt": "Short excerpt...",
        "cover_image": "cover.jpg",
        "author": {
          "id": 1,
          "username": "john",
          "avatar": "avatar.jpg"
        },
        "category": {
          "id": 1,
          "name": "Technology"
        },
        "views": 100,
        "likes": 10,
        "created_at": "2024-01-01T00:00:00",
        "tags": ["tag1", "tag2"]
      }
    ],
    "pagination": {
      "current_page": 1,
      "per_page": 20,
      "total": 100,
      "total_pages": 5,
      "has_next": true,
      "has_prev": false
    }
  }
}
```

#### 获取文章详情

```
GET /api/v3/articles/{article_id}

Response:
{
  "success": true,
  "data": {
    "id": 1,
    "title": "Article Title",
    "slug": "article-title",
    "excerpt": "Excerpt...",
    "content": "<p>Full HTML content...</p>",
    "cover_image": "cover.jpg",
    "author": {...},
    "category": {...},
    "views": 101,
    "likes": 10,
    "created_at": "2024-01-01T00:00:00",
    "updated_at": "2024-01-02T00:00:00",
    "tags": ["tag1"],
    "is_vip_only": false,
    "required_vip_level": 0
  }
}
```

#### 搜索文章

```
GET /api/v3/articles/search?keyword=python&page=1&per_page=20

Response:
{
  "success": true,
  "data": {
    "articles": [...],
    "keyword": "python",
    "pagination": {...}
  }
}
```

### 评论模块 (`/api/v3/comments`)

#### 获取文章评论

```
GET /api/v3/comments/article/{article_id}?page=1&per_page=20

Response:
{
  "success": true,
  "data": {
    "comments": [
      {
        "id": 1,
        "content": "Great article!",
        "author": {
          "id": 2,
          "username": "jane",
          "avatar": "avatar.jpg"
        },
        "created_at": "2024-01-01T12:00:00",
        "likes": 5,
        "parent_id": null
      }
    ],
    "pagination": {...}
  }
}
```

#### 发表评论

```
POST /api/v3/comments/?article_id=1&content=Great%20article!&parent_id=null
Authorization: Bearer <token>

Response:
{
  "success": true,
  "data": {
    "id": 2,
    "content": "Great article!",
    "created_at": "2024-01-01T12:00:00",
    "message": "评论发表成功"
  }
}
```

#### 点赞评论

```
POST /api/v3/comments/{comment_id}/like
Authorization: Bearer <token>

Response:
{
  "success": true,
  "data": {
    "action": "liked",  // or "unliked"
    "message": "点赞成功"
  }
}
```

### 用户模块 (`/api/v3/users`)

#### 获取用户资料

```
GET /api/v3/users/profile
Authorization: Bearer <token>

Response:
{
  "success": true,
  "data": {
    "id": 1,
    "username": "john",
    "email": "john@example.com",
    "avatar": "avatar.jpg",
    "bio": "User bio",
    "created_at": "2024-01-01T00:00:00",
    "is_active": true,
    "vip_level": 0
  }
}
```

#### 更新用户资料

```
PUT /api/v3/users/profile
Authorization: Bearer <token>
Content-Type: application/json

{
  "username": "new_username",
  "email": "new_email@example.com",
  "bio": "New bio"
}

Response:
{
  "success": true,
  "data": {
    "message": "资料更新成功",
    "user": {...}
  }
}
```

#### 获取用户统计

```
GET /api/v3/users/stats
Authorization: Bearer <token>

Response:
{
  "success": true,
  "data": {
    "articles_count": 10,
    "comments_count": 50,
    "likes_received": 100,
    "views_received": 1000
  }
}
```

### 媒体模块 (`/api/v3/media`)

#### 上传图片

```
POST /api/v3/media/upload/image
Authorization: Bearer <token>
Content-Type: multipart/form-data

file: <image_file>

Response:
{
  "success": true,
  "data": {
    "url": "http://domain.com/static/uploads/mobile/1/abc123.jpg",
    "filename": "abc123.jpg",
    "size": 102400,
    "content_type": "image/jpeg",
    "message": "图片上传成功"
  }
}
```

#### 上传文章封面

```
POST /api/v3/media/upload/article-cover
Authorization: Bearer <token>
Content-Type: multipart/form-data

file: <image_file>

Response:
{
  "success": true,
  "data": {
    "url": "http://domain.com/static/uploads/covers/1/cover_abc123.jpg",
    "filename": "cover_abc123.jpg",
    "size": 51200,
    "message": "封面上传成功"
  }
}
```

### 分类模块 (`/api/v3/categories`)

#### 获取分类列表

```
GET /api/v3/categories/list

Response:
{
  "success": true,
  "data": {
    "categories": [
      {
        "id": 1,
        "name": "Technology",
        "description": "Tech articles",
        "slug": "technology",
        "parent_id": null
      }
    ]
  }
}
```

## 错误响应

所有错误响应遵循统一格式：

```json
{
  "success": false,
  "error": "错误描述信息"
}
```

常见错误码：

- 400: 请求参数错误
- 401: 未认证或token无效
- 403: 权限不足
- 404: 资源不存在
- 500: 服务器内部错误

## 分页参数

所有列表接口支持分页：

- `page`: 页码（从1开始）
- `per_page`: 每页数量（默认20，最大50）

## 注意事项

1. 所有时间字段使用ISO 8601格式
2. 图片URL为完整路径，可直接使用
3. 评论内容支持纯文本，前端可自行渲染
4. 文章内容为HTML格式，可直接渲染
5. 上传文件大小限制：普通图片10MB，封面图片5MB
