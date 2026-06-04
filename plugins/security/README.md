# 安全防护中心 (Security)

综合安全防护系统，整合了恶意代码扫描、文件完整性监控、XSS/SQL注入防护、速率限制、IP黑白名单、登录保护等功能。

## 功能特性

### 1. 恶意代码扫描器

- 检测可疑代码模式（eval、base64_decode、system/exec等）
- 识别Web Shell特征
- SQL注入模式检测
- 定时自动扫描
- 已知安全文件白名单

### 2. 文件完整性监控

- 基于SHA256哈希的文件监控
- 检测文件新增、修改、删除
- 支持自定义监控目录
- 实时变更告警

### 3. XSS/SQL注入防护

- 实时请求过滤
- 检测常见XSS攻击模式
- 检测SQL注入尝试
- 输出内容清理

### 4. 速率限制

- 基于IP的请求频率控制
- 可配置时间窗口和最大请求数
- 防止DDoS和暴力破解

### 5. IP黑白名单

- IP黑名单阻止恶意访问
- IP白名单限制访问范围
- 支持批量导入导出

### 6. 登录保护

- 登录失败次数限制
- 账户自动锁定机制
- 可配置锁定时长
- 防止暴力破解

### 7. 安全日志审计

- 记录所有安全事件
- 支持事件类型过滤
- 日志自动轮转（保留90天）
- 数据库持久化存储

### 8. 完整安全扫描

- 一键执行全面安全检查
- 多模块协同扫描
- 生成详细扫描报告
- 提供修复建议

## 安装

插件已内置，在管理后台启用即可。

## 配置

### 恶意代码扫描设置

```python
'enable_malware_scan': True,           # 启用扫描
'scan_interval_hours': 24,             # 扫描间隔（小时）
'auto_scan_enabled': True,             # 自动扫描
'scan_directories': ['src', 'shared'], # 扫描目录
'max_file_size_mb': 10,                # 最大文件大小
```

### 防护设置

```python
'enable_xss_protection': True,                    # XSS防护
'enable_sql_injection_detection': True,           # SQL注入检测
'enable_rate_limiting': True,                     # 速率限制
'rate_limit_requests': 60,                        # 每分钟最大请求数
'rate_limit_window': 60,                          # 时间窗口（秒）
```

### IP黑白名单

```python
'enable_ip_blacklist': True,          # 启用黑名单
'enable_ip_whitelist': False,         # 启用白名单
'ip_blacklist': '192.168.1.100,...',  # 黑名单IP列表
'ip_whitelist': '10.0.0.1,...',       # 白名单IP列表
```

### 登录保护

```python
'enable_login_lockout': True,    # 启用登录锁定
'max_login_attempts': 5,         # 最大尝试次数
'lockout_duration': 30,          # 锁定时长（分钟）
```

### 文件完整性监控

```python
'enable_file_integrity': True,                      # 启用监控
'monitored_directories': ['src', 'shared', 'apps'], # 监控目录
```

## API接口

### 获取仪表板数据

```
GET /api/plugins/security/dashboard
```

### 执行完整安全扫描

```
POST /api/plugins/security/full-scan
```

### 获取安全日志

```
GET /api/plugins/security/logs?limit=100&event_type=xss_detected
```

### 更新文件快照

```
POST /api/plugins/security/update-snapshot
```

### 立即执行扫描

```
POST /api/plugins/security/scan-now
```

## 使用示例

### 查看安全状态

```python
from plugins.security.plugin import plugin

# 获取仪表板数据
dashboard = plugin.get_dashboard_data()
print(f"已扫描文件: {dashboard['scan_stats']['total_files_scanned']}")
print(f"发现威胁: {dashboard['scan_stats']['threats_found']}")
```

### 执行安全扫描

```python
# 执行完整扫描
result = plugin.run_full_security_scan()
print(f"扫描状态: {result['overall_status']}")
print(f"耗时: {result['duration_seconds']}秒")

# 查看各模块结果
for module_name, module_result in result['modules'].items():
    print(f"{module_name}: {module_result}")
```

### 查看安全日志

```python
# 获取最近100条日志
logs = plugin.get_security_logs(limit=100)

# 获取特定类型的日志
xss_logs = plugin.get_security_logs(limit=50, event_type='xss_detected')
```

## 数据库表结构

### scan_results - 扫描结果表

```sql
CREATE TABLE scan_results (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    scan_time TEXT NOT NULL,
    files_scanned INTEGER DEFAULT 0,
    threats_found INTEGER DEFAULT 0,
    threats_data TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

### security_logs - 安全日志表

```sql
CREATE TABLE security_logs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    event_type TEXT NOT NULL,
    timestamp TEXT NOT NULL,
    details TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

### threats - 威胁记录表

```sql
CREATE TABLE threats (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    file_path TEXT NOT NULL,
    threat_type TEXT NOT NULL,
    severity TEXT NOT NULL,
    description TEXT,
    detected_at TEXT NOT NULL,
    status TEXT DEFAULT 'active',
    resolved_at TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

## 注意事项

1. **性能影响**：大规模文件扫描可能影响系统性能，建议在低峰期执行
2. **误报处理**：某些合法代码可能被标记为可疑，请根据实际情况调整规则
3. **日志管理**：定期清理旧日志，避免数据库过大
4. **白名单维护**：及时更新已知安全文件哈希，减少重复扫描
5. **IP名单**：谨慎使用白名单模式，确保不会阻止合法用户

## 故障排除

### 扫描未执行

- 检查 `enable_malware_scan` 是否启用
- 检查 `auto_scan_enabled` 是否启用
- 查看日志确认是否有错误

### 误报过多

- 将合法文件添加到已知安全哈希
- 调整可疑代码模式规则
- 排除特定目录或文件

### 性能问题

- 减少扫描频率
- 缩小扫描目录范围
- 增加文件大小限制

## 版本历史

### v2.0.0 (当前版本)

- 整合 malware-scanner、security-guard、security-pro 三个插件
- 统一配置管理
- 优化性能
- 增强日志记录

### v1.0.0

- 初始版本（已废弃）

## 许可证

MIT License

## 支持

如有问题，请访问 FastBlog 官方文档或提交 Issue。
