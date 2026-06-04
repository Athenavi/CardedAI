# FastBlog Cloud Upgrade Plugin

一键升级系统插件,提供安全、可靠的版本更新和回滚机制。

## ✨ 核心功能

### 1. 10步升级流程

1. **升级前健康检查** - 磁盘空间、服务状态、数据库连接
2. **创建备份** - 文件备份 + 数据库备份
3. **下载更新包** - 从 GitHub/本地/自定义服务器
4. **验证完整性** - ZIP文件完整性测试
5. **兼容性检查** - Python版本、依赖、数据库schema、插件
6. **停止服务** - 安全停止Web服务
7. **应用更新** - 解压并替换文件
8. **数据库迁移** - 运行Alembic迁移
9. **启动服务** - 重启Web服务
10. **升级后验证** - 版本确认、服务检查、API测试

### 2. 多更新源支持

- **GitHub Releases**: 自动检查最新版本
- **本地更新包**: 从 releases/ 目录读取
- **自定义服务器**: 私有更新服务器

### 3. 安全回滚机制

- 升级失败自动回滚
- 保留最近3个版本的备份
- 文件和数据库完整恢复
- 回滚后验证

### 4. 兼容性检查

- Python版本检查 (最低3.10)
- 依赖包版本冲突检测
- 数据库schema兼容性
- 已安装插件兼容性

### 5. 健康检查

- 磁盘空间检查 (最低1GB)
- 关键服务状态 (PostgreSQL/Redis/Nginx)
- API端点可用性
- 数据库连接测试

### 6. 升级历史

- 记录所有升级操作
- 包含成功/失败状态
- 记录执行时长
- 最多保存100条记录

## 📦 安装

```bash
# 插件已包含在 plugins/cloud-upgrade 目录
# 在管理后台激活即可
```

## ⚙️ 配置

### 基础配置

```json
{
  "enabled": true,
  "update_sources": {
    "github": {
      "enabled": true,
      "repo": "Athenavi/fast_blog",
      "check_interval_hours": 24
    },
    "local": {
      "enabled": true,
      "releases_dir": "releases"
    }
  },
  "upgrade_policy": {
    "auto_check": true,
    "auto_download": false,
    "auto_install": false,
    "backup_before_upgrade": true,
    "auto_rollback_on_failure": true,
    "require_confirmation": true
  }
}
```

### 兼容性检查配置

```json
{
  "compatibility_check": {
    "check_python_version": true,
    "min_python_version": "3.10.0",
    "check_dependencies": true,
    "check_database_schema": true,
    "check_plugins_compatibility": true
  }
}
```

### 健康检查配置

```json
{
  "health_check": {
    "pre_upgrade": true,
    "post_upgrade": true,
    "check_services": ["postgresql", "redis", "nginx"],
    "check_api_endpoints": true,
    "check_disk_space": true,
    "min_disk_space_mb": 1024
  }
}
```

## 🚀 使用

### 检查更新

```bash
curl -X GET http://localhost:9421/api/v2/cloud/upgrade/check \
  -H "Authorization: Bearer YOUR_TOKEN"
```

响应示例:

```json
{
  "has_update": true,
  "current_version": "1.0.0",
  "available_versions": [
    {
      "source": "github",
      "version": "1.2.0",
      "name": "v1.2.0 - New Features",
      "published_at": "2024-01-15T10:00:00Z",
      "description": "Release notes..."
    }
  ],
  "recommended_version": {
    "version": "1.2.0",
    "source": "github"
  }
}
```

### 开始升级

```bash
curl -X POST http://localhost:9421/api/v2/cloud/upgrade/start \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "version": "1.2.0",
    "source": "github",
    "backup_before": true,
    "auto_rollback": true
  }'
```

### 查询升级状态

```bash
curl -X GET http://localhost:9421/api/v2/cloud/upgrade/status \
  -H "Authorization: Bearer YOUR_TOKEN"
```

### 回滚升级

```bash
curl -X POST http://localhost:9421/api/v2/cloud/upgrade/rollback \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "confirm": true,
    "reason": "Performance issues after upgrade"
  }'
```

### 查看升级历史

```bash
curl -X GET "http://localhost:9421/api/v2/cloud/upgrade/history?limit=10" \
  -H "Authorization: Bearer YOUR_TOKEN"
```

## 📊 API 端点

| 端点                               | 方法   | 描述     |
|----------------------------------|------|--------|
| `/api/v2/cloud/upgrade/check`    | GET  | 检查可用更新 |
| `/api/v2/cloud/upgrade/start`    | POST | 开始升级   |
| `/api/v2/cloud/upgrade/status`   | GET  | 查询状态   |
| `/api/v2/cloud/upgrade/rollback` | POST | 回滚升级   |
| `/api/v2/cloud/upgrade/history`  | GET  | 升级历史   |

## 🔒 安全性

### 升级前安全措施

1. ✅ 强制备份 (可配置)
2. ✅ 完整性验证 (ZIP checksum)
3. ✅ 兼容性检查
4. ✅ 健康检查
5. ✅ 需要管理员确认

### 升级中安全措施

1. ✅ 原子性操作
2. ✅ 错误即时检测
3. ✅ 自动回滚机制
4. ✅ 详细日志记录

### 升级后安全措施

1. ✅ 版本验证
2. ✅ 服务健康检查
3. ✅ API端点测试
4. ✅ 数据库一致性检查

## 🐛 故障排查

### 升级失败

**问题**: 升级过程中断

**解决**:

1. 检查升级日志: `logs/cloud_upgrade.log`
2. 查看失败步骤
3. 检查备份是否完整
4. 手动执行回滚或重试

### 回滚失败

**问题**: 回滚操作失败

**解决**:

1. 检查备份目录是否存在
2. 验证备份文件完整性
3. 手动恢复文件
4. 手动恢复数据库

### 兼容性问题

**问题**: 兼容性检查失败

**解决**:

1. 检查Python版本: `python --version`
2. 更新依赖: `pip install -r requirements.txt`
3. 检查插件版本兼容性
4. 联系开发者获取支持

## 📝 最佳实践

### 1. 升级前准备

- 阅读发布说明
- 在测试环境先升级
- 确保有足够的磁盘空间
- 通知相关人员

### 2. 升级时机

- 选择低峰时段
- 预留足够的维护窗口
- 避免业务高峰期

### 3. 备份策略

- 启用自动备份
- 验证备份完整性
- 保留多个版本备份
- 定期清理旧备份

### 4. 监控升级

- 实时查看升级进度
- 关注错误日志
- 准备好回滚方案
- 升级后立即验证

## 🔄 升级流程详解

### Step 1: 升级前健康检查

```
✓ 磁盘空间 >= 1GB
✓ PostgreSQL 运行正常
✓ Redis 运行正常
✓ Nginx 运行正常
✓ API 端点可访问
```

### Step 2: 创建备份

```
✓ 备份 src/ 目录
✓ 备份 shared/ 目录
✓ 备份 config/ 目录
✓ 备份 plugins/ 目录
✓ 备份 .env 文件
✓ 导出数据库 (pg_dump)
```

### Step 3-5: 下载和验证

```
✓ 下载更新包
✓ 验证文件大小
✓ 测试 ZIP 完整性
✓ 检查 Python 版本
✓ 检查依赖兼容性
```

### Step 6-10: 执行升级

```
✓ 停止 FastBlog 服务
✓ 解压更新包
✓ 替换文件
✓ 运行数据库迁移
✓ 启动服务
✓ 验证版本
✓ 检查服务状态
✓ 测试 API 端点
```

## 🧪 测试升级

### 使用 Staging 环境

1. 克隆生产环境到 staging
2. 在 staging 执行升级
3. 验证功能和性能
4. 确认无问题后再升级生产

### 本地测试

```bash
# 创建测试环境
python scripts/build_release.py --version 1.2.0 --output releases/

# 本地测试升级
curl -X POST http://localhost:9421/api/v2/cloud/upgrade/start \
  -d '{"version": "1.2.0", "source": "local"}'
```

## 📈 升级统计

### 成功率指标

- 目标升级成功率: > 99%
- 自动回滚成功率: 100%
- 平均升级时间: < 5分钟
- 备份创建时间: < 2分钟

### 历史记录分析

```bash
# 查看升级统计
curl -X GET http://localhost:9421/api/v2/cloud/upgrade/history \
  | jq '[.[] | select(.success == true)] | length'
```

## 🤝 贡献

欢迎提交 Issue 和 Pull Request!

## 📄 许可证

Apache License 2.0

---

**FastBlog Team** - 让升级更安全、更简单
