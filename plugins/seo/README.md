# SEO优化中心 (SEO)

综合SEO优化系统，整合了元标签管理、Sitemap生成、Robots.txt管理、重定向管理、404监控、Schema结构化数据等功能。

## 功能特性

### 1. 元标签管理

- 自动生成title、description、keywords
- Open Graph标签支持
- Twitter Card支持
- 规范URL管理

### 2. Sitemap生成

- XML Sitemap自动生成
- 支持图片索引
- 可配置更新频率
- 文章发布时自动更新

### 3. Robots.txt管理

- 可视化编辑
- 自动生成基础规则
- 支持自定义配置

### 4. 重定向管理

- 301/302重定向规则
- 批量导入导出
- 激活/停用控制

### 5. 404监控

- 自动追踪404错误
- 统计错误次数
- 提供修复建议

### 6. Schema结构化数据

- Article Schema
- Organization Schema
- Breadcrumb Schema
- WebSite Schema
- 自动注入到页面

## 安装

插件已内置，在管理后台启用即可。

## 配置

### 元标签设置

```python
'auto_generate_meta': True,  # 自动生成
'site_name': 'FastBlog',  # 网站名称
'canonical_url_base': 'https://example.com',  # 规范URL
'twitter_handle': 'your_twitter',  # Twitter账号
```

### Sitemap设置

```python
'include_images_in_sitemap': True,  # 包含图片
'sitemap_update_frequency': 'daily',  # 更新频率
```

### Schema设置

```python
'enable_schema': True,  # 启用Schema
'enable_article_schema': True,  # 文章Schema
'enable_organization_schema': True,  # 组织Schema
'organization_name': 'Your Company',  # 组织名称
'organization_logo': 'https://...',  # Logo URL
```

## API接口

### 获取仪表板数据

```
GET /api/plugins/seo/dashboard
```

### 重新生成Sitemap

```
POST /api/plugins/seo/regenerate-sitemap
```

### 添加重定向规则

```
POST /api/plugins/seo/redirect
{
  "from_url": "/old-page",
  "to_url": "/new-page",
  "status_code": 301
}
```

### 获取SEO报告

```
GET /api/plugins/seo/report
```

## 使用示例

### 查看SEO状态

```python
from plugins.seo.plugin import plugin

# 获取仪表板数据
dashboard = plugin.get_dashboard_data()
print(f"重定向规则: {dashboard['redirects_count']}")
print(f"404错误: {dashboard['404_errors_count']}")
```

### 添加重定向

```python
# 添加301重定向
plugin.add_redirect('/old-article', '/new-article', 301)

# 删除重定向
plugin.remove_redirect('/old-article')
```

### 生成robots.txt

```python
# 生成并保存robots.txt
plugin.save_robots_txt()

# 自定义robots.txt
custom_content = """
User-agent: *
Disallow: /admin/
"""
plugin.save_robots_txt(custom_content)
```

### 查看404错误

```python
# 获取最多的404错误
top_errors = plugin.get_top_404_errors(limit=20)
for error in top_errors:
    print(f"{error['url']}: {error['count']}次")
```

## 注意事项

1. **Sitemap位置**：生成的sitemap.xml保存在 `public/sitemap.xml`
2. **robots.txt位置**：保存在 `public/robots.txt`
3. **重定向性能**：大量重定向规则可能影响性能，建议定期清理
4. **404监控**：生产环境建议开启，及时发现和修复死链
5. **Schema验证**：使用Google Rich Results Test验证Schema是否正确

## 故障排除

### Sitemap未生成

- 检查是否有文章数据
- 确认 `public` 目录可写
- 查看日志是否有错误

### 元标签未显示

- 检查 `auto_generate_meta` 是否启用
- 确认主题模板正确调用钩子
- 清除浏览器缓存

### Schema未生效

- 使用Google Rich Results Test验证
- 检查JSON格式是否正确
- 确认页面类型匹配

## 版本历史

### v2.0.0 (当前版本)

- 整合 seo-optimizer、advanced-seo、schema-markup 三个插件
- 统一配置管理
- 增强Schema支持
- 优化Sitemap生成性能

### v1.0.0

- 初始版本（已废弃）

## 许可证

MIT License

## 支持

如有问题，请访问 FastBlog 官方文档或提交 Issue。
