# 性能优化中心 (OPT)

综合性能优化系统，整合了页面缓存、性能监控、图片优化、CDN管理、懒加载等功能。

## 功能特性

### 1. 页面缓存

- 内存和文件两级缓存
- 智能缓存失效策略
- 可配置的排除路径
- 自动缓存命中率统计

### 2. 性能监控

- 页面加载时间追踪
- 数据库查询监控
- 慢查询检测
- 性能告警系统

### 3. 图片优化

- 自动压缩图片
- WebP格式转换
- 尺寸调整
- 优化统计

### 4. CDN管理

- 自动URL转换
- HTML图片批量转换
- 支持主流CDN服务商
- 缓存刷新

### 5. 懒加载

- 图片延迟加载
- 减少初始页面负载
- 提升首屏加载速度

## 安装

插件已内置，在管理后台启用即可。

## 配置

### 页面缓存设置

```python
'enable_page_cache': True,           # 启用缓存
'cache_ttl': 3600,                   # 缓存时长（秒）
'max_cache_size': 1000,              # 最大缓存条目数
'excluded_paths': ['/admin', '/api'] # 排除路径
```

### 性能监控设置

```python
'enable_performance_monitor': True,  # 启用监控
'slow_query_threshold': 100,         # 慢查询阈值（毫秒）
'page_load_threshold': 2,            # 页面加载阈值（秒）
'sampling_rate': 100,                # 采样率（%）
```

### CDN设置

```python
'enable_cdn': True,                  # 启用CDN
'cdn_base_url': 'https://cdn.example.com',
'cdn_auto_purge': True,              # 自动刷新
```

### 图片优化设置

```python
'enable_image_optimization': True,   # 启用优化
'auto_compress': True,               # 自动压缩
'compression_quality': 80,           # 压缩质量
'convert_to_webp': True,             # 转WebP
'max_width': 1920,                   # 最大宽度
'max_height': 1080,                  # 最大高度
```

### 懒加载设置

```python
'enable_lazy_load': True,            # 启用懒加载
'lazy_load_threshold': 300,          # 阈值（像素）
```

## API接口

### 获取仪表板数据

```
GET /api/plugins/opt/dashboard
```

### 清除所有缓存

```
POST /api/plugins/opt/clear-cache
```

### 获取性能报告

```
GET /api/plugins/opt/report?hours=24
```

## 使用示例

### 查看性能状态

```python
from plugins.opt.plugin import plugin

# 获取仪表板数据
dashboard = plugin.get_dashboard_data()
print(f"缓存命中率: {dashboard['cache_stats']['hit_rate']}%")
print(f"平均加载时间: {dashboard['performance_stats']['avg_load_time']}s")
```

### 获取性能报告

```python
# 获取最近24小时报告
report = plugin.get_performance_report(hours=24)
print(f"总请求数: {report['total_requests']}")
print(f"P95加载时间: {report['p95_load_time']}s")
```

### CDN URL转换

```python
# 转换单个URL
cdn_url = plugin.convert_to_cdn_url('/static/image.jpg')

# 转换HTML中的图片
html_with_cdn = plugin.convert_html_images_to_cdn(html_content)
```

### 添加懒加载

```python
# 为HTML图片添加懒加载
lazy_html = plugin.add_lazy_load_to_images(html_content)
```

## 注意事项

1. **缓存一致性**：内容更新时会自动清除缓存，确保用户看到最新内容
2. **性能开销**：性能监控会记录所有请求，生产环境建议调整采样率
3. **CDN配置**：使用前需要先配置CDN服务商
4. **图片优化**：大尺寸图片优化可能耗时较长，建议异步处理
5. **存储空间**：定期清理旧缓存文件，避免占用过多磁盘空间

## 故障排除

### 缓存未生效

- 检查 `enable_page_cache` 是否启用
- 确认请求路径不在排除列表中
- 查看缓存目录权限

### 性能监控无数据

- 检查 `enable_performance_monitor` 是否启用
- 确认钩子正确注册
- 查看日志是否有错误

### CDN不工作

- 检查 `enable_cdn` 是否启用
- 确认 `cdn_base_url` 配置正确
- 验证CDN服务商配置

## 版本历史

### v2.0.0 (当前版本)

- 整合 page-cache、performance-monitor、image-optimizer、cdn-manager、image-lazy-load 五个插件
- 统一配置管理
- 优化性能
- 增强监控能力

### v1.0.0

- 初始版本（已废弃）

## 许可证

MIT License

## 支持

如有问题，请访问 FastBlog 官方文档或提交 Issue。
