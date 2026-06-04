# FastBlog Cloud CDN Plugin

多云CDN管理服务插件,为 FastBlog 提供高性能内容分发解决方案。

## ✨ 核心功能

### 1. 多云CDN支持

- **Cloudflare**: 全球CDN网络,免费套餐友好
- **阿里云 CDN**: 中国大陆优化,稳定可靠
- **腾讯云 CDN**: 华南地区优势,性价比高

### 2. 智能缓存策略

- 静态资源长期缓存 (CSS/JS/字体: 1年)
- 图片中期缓存 (30天)
- HTML短期缓存 (1小时)
- API动态缓存 (5分钟)
- 可自定义正则匹配规则

### 3. 缓存管理

- **批量清除**: 支持一次性清除多个URL
- **缓存预热**: 主动将内容推送到CDN节点
- **自动清除**: 内容更新时自动清除相关缓存
- **限制处理**: 自动分批处理大批量URL

### 4. URL自动转换

- HTML中的图片/脚本/样式URL自动转换为CDN URL
- 支持排除特定路径 (/admin, /api等)
- 避免重复转换和外部链接误转换

### 5. 性能监控

- 带宽使用统计
- 请求数量分析
- 缓存命中率监控
- 威胁检测统计
- 多时间周期查看 (24h/7d/30d)

### 6. 自动优化 (计划中)

- 图片自动转换为WebP格式
- 图片压缩和质量调整
- 响应式图片srcset生成
- CSS/JS压缩

## 📦 安装

### 依赖安装

```bash
# Cloudflare (无需额外依赖,使用aiohttp)
pip install aiohttp

# 阿里云 CDN
pip install aliyun-python-sdk-cdn aliyun-python-sdk-core

# 腾讯云 CDN
pip install tencentcloud-sdk-python
```

## ⚙️ 配置

### Cloudflare 配置

1. 登录 [Cloudflare Dashboard](https://dash.cloudflare.com/)
2. 选择你的域名
3. 进入 "Overview" -> 复制 "Zone ID"
4. 进入 "My Profile" -> "API Tokens" -> 创建新的 Token
    - 权限: Zone -> Cache Purge -> Purge
    - 区域资源: 包含你的域名

```json
{
  "enabled": true,
  "primary_provider": "cloudflare",
  "providers": {
    "cloudflare": {
      "enabled": true,
      "api_token": "YOUR_API_TOKEN",
      "zone_id": "YOUR_ZONE_ID"
    }
  },
  "url_conversion": {
    "enabled": true,
    "cdn_base_url": "https://cdn.example.com",
    "auto_convert_html": true
  }
}
```

### 阿里云 CDN 配置

```json
{
  "enabled": true,
  "primary_provider": "aliyun",
  "providers": {
    "aliyun": {
      "enabled": true,
      "access_key_id": "YOUR_ACCESS_KEY_ID",
      "access_key_secret": "YOUR_ACCESS_KEY_SECRET",
      "domain": "cdn.example.com"
    }
  }
}
```

### 腾讯云 CDN 配置

```json
{
  "enabled": true,
  "primary_provider": "tencent",
  "providers": {
    "tencent": {
      "enabled": true,
      "secret_id": "YOUR_SECRET_ID",
      "secret_key": "YOUR_SECRET_KEY",
      "domain": "cdn.example.com"
    }
  }
}
```

## 🚀 使用

### 清除缓存

```bash
# 通过 API
curl -X POST http://localhost:9421/api/v2/cloud/cdn/purge \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "urls": [
      "/static/css/main.css",
      "/static/js/app.js",
      "/images/logo.png"
    ],
    "provider": "cloudflare"
  }'
```

### 预热缓存

```bash
curl -X POST http://localhost:9421/api/v2/cloud/cdn/prefetch \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "urls": [
      "https://cdn.example.com/article/popular-article"
    ],
    "priority": "high"
  }'
```

### 获取分析数据

```bash
curl -X GET "http://localhost:9421/api/v2/cloud/cdn/analytics?period=7d" \
  -H "Authorization: Bearer YOUR_TOKEN"
```

响应示例:

```json
{
  "success": true,
  "provider": "cloudflare",
  "period": "7d",
  "bandwidth": 1073741824,
  "requests": 100000,
  "cached_requests": 85000,
  "uncached_requests": 15000,
  "cache_hit_ratio": 0.85,
  "threats_detected": 12
}
```

### 测试连接

```bash
curl -X POST http://localhost:9421/api/v2/cloud/cdn/test \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "provider": "cloudflare"
  }'
```

## 📊 API 端点

| 端点                            | 方法   | 描述      |
|-------------------------------|------|---------|
| `/api/v2/cloud/cdn/purge`     | POST | 清除CDN缓存 |
| `/api/v2/cloud/cdn/prefetch`  | POST | 预热CDN缓存 |
| `/api/v2/cloud/cdn/analytics` | GET  | 获取分析数据  |
| `/api/v2/cloud/cdn/test`      | POST | 测试连接    |
| `/api/v2/cloud/cdn/config`    | PUT  | 更新配置    |
| `/api/v2/cloud/cdn/stats`     | GET  | 获取统计数据  |

## 🔧 缓存策略配置

### 默认策略

```json
{
  "cache_strategies": {
    "static": {
      "pattern": "\\.(css|js|png|jpg|jpeg|gif|svg|woff|woff2|ttf|eot)$",
      "ttl": 31536000,
      "cache_control": "public, max-age=31536000, immutable"
    },
    "images": {
      "pattern": "\\.(png|jpg|jpeg|gif|webp|svg)$",
      "ttl": 2592000,
      "cache_control": "public, max-age=2592000"
    },
    "html": {
      "pattern": "\\.html?$",
      "ttl": 3600,
      "cache_control": "public, max-age=3600"
    },
    "api": {
      "pattern": "^/api/",
      "ttl": 300,
      "cache_control": "private, max-age=300"
    }
  }
}
```

### 自定义策略

你可以根据需要添加或修改策略:

```json
{
  "cache_strategies": {
    "videos": {
      "pattern": "\\.(mp4|webm|ogg)$",
      "ttl": 604800,
      "cache_control": "public, max-age=604800"
    },
    "downloads": {
      "pattern": "\\.(pdf|zip|tar\\.gz)$",
      "ttl": 86400,
      "cache_control": "public, max-age=86400"
    }
  }
}
```

## 🎯 最佳实践

### 1. CDN URL 配置

确保 `cdn_base_url` 正确配置:

```json
{
  "url_conversion": {
    "cdn_base_url": "https://cdn.yourdomain.com",
    "excluded_paths": [
      "/admin",
      "/api/internal"
    ]
  }
}
```

### 2. 缓存清除策略

- **文章更新**: 自动清除相关文章页面
- **主题修改**: 手动清除所有静态资源
- **紧急修复**: 使用通配符清除整个目录

### 3. 预热重要内容

在发布重要文章前预热:

```python
# 预热热门文章
await cdn_plugin.prefetch_urls([
    'https://cdn.example.com/article/popular-1',
    'https://cdn.example.com/article/popular-2',
])
```

### 4. 监控缓存命中率

目标缓存命中率:

- 静态资源: > 95%
- 图片: > 90%
- HTML: > 70%
- API: > 50%

## 🔒 安全性

### API Token 安全

- ✅ 使用环境变量存储敏感信息
- ✅ 定期轮换 API Token
- ✅ 限制 Token 权限 (最小权限原则)
- ✅ 不要在代码中硬编码密钥

### 示例 (.env)

```bash
CLOUDFLARE_API_TOKEN=your_api_token_here
CLOUDFLARE_ZONE_ID=your_zone_id_here
ALIYUN_ACCESS_KEY_ID=your_access_key_id
ALIYUN_ACCESS_KEY_SECRET=your_access_key_secret
```

## 🐛 故障排查

### 清除缓存失败

**问题**: 返回 403 Forbidden

**解决**:

1. 检查 API Token 权限
2. 确认 Zone ID 正确
3. 验证 Token 未过期

### URL 转换不生效

**问题**: HTML 中的 URL 没有转换为 CDN URL

**解决**:

1. 检查 `url_conversion.enabled` 是否为 true
2. 确认 `cdn_base_url` 已配置
3. 检查 URL 是否在 `excluded_paths` 中
4. 查看日志确认转换是否执行

### 分析数据为空

**问题**: get_analytics 返回空数据

**解决**:

1. 确认 CDN 已有流量
2. 检查时间周期设置
3. 验证 API 权限包含 Analytics 读取

## 📈 性能指标

### Cloudflare 限制

- 单次清除最多 30 个 URL
- 单次预热最多 10 个 URL
- API 速率限制: 1200 请求/5分钟

### 阿里云 CDN 限制

- 单次刷新最多 100 个 URL
- 单日刷新配额: 根据套餐而定

### 腾讯云 CDN 限制

- 单次刷新最多 1000 个 URL
- 单日刷新配额: 根据套餐而定

## 🔄 多云策略

### 主备方案

```json
{
  "primary_provider": "cloudflare",
  "providers": {
    "cloudflare": {
      "enabled": true,
      "...": "..."
    },
    "aliyun": {
      "enabled": true,
      "...": "...",
      "note": "作为中国大陆备用"
    }
  }
}
```

### 地域路由

- 国际用户: Cloudflare
- 中国大陆用户: 阿里云/腾讯云

(需要配合 DNS 智能解析)

## 🧪 测试

### 单元测试

```bash
pytest tests/plugins/test_cloud_cdn.py -v
```

### 集成测试

1. 配置测试环境的 CDN
2. 上传测试文件
3. 执行清除和预热操作
4. 验证缓存状态

## 📝 开发者指南

### 添加新的 CDN 提供商

1. 创建新的 Provider 类继承 `CDNProvider`
2. 实现所有抽象方法
3. 在 `CloudCDNPlugin._get_provider()` 中注册
4. 添加配置 schema

```python
class CustomCDN(CDNProvider):
    def __init__(self, config: Dict[str, str]):
        self.api_key = config.get('api_key', '')

    async def purge_cache(self, urls: List[str]) -> Dict[str, Any]:
        # 实现清除逻辑
        pass

    # ... 实现其他方法
```

## 🤝 贡献

欢迎提交 Issue 和 Pull Request!

## 📄 许可证

Apache License 2.0

---

**FastBlog Team** - 为您的博客加速
