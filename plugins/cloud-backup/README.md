# FastBlog Cloud Backup Plugin

增强版云备份服务插件,为 FastBlog 提供企业级数据保护解决方案。

## ✨ 核心功能

### 1. 增量备份

- 基于 WAL (Write-Ahead Logging) 的增量备份
- 仅备份变更数据,减少存储空间和备份时间
- 自动追踪文件哈希变化

### 2. 文件和资源备份

- 媒体文件自动备份
- 主题和插件文件备份
- 用户上传内容备份
- 支持自定义排除模式

### 3. 多策略调度

- **每日备份**: 增量备份,保留7天
- **每周备份**: 完整备份,保留30天
- **每月备份**: 完整备份,保留365天
- Cron 表达式灵活配置

### 4. 备份验证

- 自动验证备份完整性
- 数据库 dump 文件验证
- 压缩包完整性检查
- 元数据一致性验证

### 5. 多云存储支持

- Amazon S3
- 阿里云 OSS
- 腾讯云 COS
- 支持跨地域复制

### 6. 智能通知

- 备份成功/失败通知
- 多渠道支持 (邮件/Webhook)
- 可配置的告警规则

## 📦 安装

```bash
# 插件已包含在 plugins/cloud-backup 目录
# 在管理后台激活即可
```

### 依赖安装

```bash
# S3 支持
pip install boto3

# 阿里云 OSS 支持
pip install oss2

# 腾讯云 COS 支持
pip install cos-python-sdk-v5
```

## ⚙️ 配置

### 基础配置

在管理后台 `Plugins > Cloud Backup > Settings` 中配置:

```json
{
  "db_backup_enabled": true,
  "file_backup_enabled": true,
  "policies": {
    "daily": {
      "enabled": true,
      "schedule": "0 2 * * *",
      "type": "incremental",
      "retention_days": 7
    },
    "weekly": {
      "enabled": true,
      "schedule": "0 3 * * 0",
      "type": "full",
      "retention_days": 30
    },
    "monthly": {
      "enabled": true,
      "schedule": "0 4 1 * *",
      "type": "full",
      "retention_days": 365
    }
  }
}
```

### 云存储配置

#### Amazon S3

```json
{
  "cloud_storage": {
    "enabled": true,
    "primary_provider": "s3",
    "providers": {
      "s3": {
        "bucket": "my-fastblog-backups",
        "access_key": "YOUR_ACCESS_KEY",
        "secret_key": "YOUR_SECRET_KEY",
        "region": "us-east-1"
      }
    }
  }
}
```

#### 阿里云 OSS

```json
{
  "cloud_storage": {
    "enabled": true,
    "primary_provider": "oss",
    "providers": {
      "oss": {
        "bucket": "my-fastblog-backups",
        "access_key": "YOUR_ACCESS_KEY",
        "secret_key": "YOUR_SECRET_KEY",
        "region": "oss-cn-hangzhou"
      }
    }
  }
}
```

## 🚀 使用

### 手动创建备份

```bash
# 通过 API
curl -X POST http://localhost:9421/api/v2/cloud/backup/create \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "backup_type": "full",
    "targets": ["database", "files"],
    "upload_to_cloud": true
  }'
```

### 列出备份

```bash
curl -X GET http://localhost:9421/api/v2/cloud/backup/list \
  -H "Authorization: Bearer YOUR_TOKEN"
```

### 恢复备份

```bash
curl -X POST http://localhost:9421/api/v2/cloud/backup/backup_full_20240101_020000/restore \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "target": "both",
    "drop_existing": false
  }'
```

### 验证备份

```bash
curl -X POST http://localhost:9421/api/v2/cloud/backup/backup_full_20240101_020000/verify \
  -H "Authorization: Bearer YOUR_TOKEN"
```

## 📊 API 端点

| 端点                                  | 方法   | 描述   |
|-------------------------------------|------|------|
| `/api/v2/cloud/backup/create`       | POST | 创建备份 |
| `/api/v2/cloud/backup/list`         | GET  | 列出备份 |
| `/api/v2/cloud/backup/{id}/restore` | POST | 恢复备份 |
| `/api/v2/cloud/backup/{id}/verify`  | POST | 验证备份 |
| `/api/v2/cloud/backup/policy`       | PUT  | 更新策略 |
| `/api/v2/cloud/backup/stats`        | GET  | 备份统计 |

## 🔒 安全性

- ✅ 备份文件加密 (AES-256)
- ✅ SSL/TLS 传输加密
- ✅ API 密钥安全存储
- ✅ 访问控制和权限管理
- ✅ 操作审计日志

## 🧪 测试

### 运行单元测试

```bash
pytest tests/plugins/test_cloud_backup.py -v
```

### 备份恢复演练

建议定期执行备份恢复演练:

1. 创建测试备份
2. 在隔离环境中恢复
3. 验证数据完整性
4. 记录演练结果

## 📝 最佳实践

### 1. 3-2-1 备份原则

- **3** 份数据副本
- **2** 种不同介质
- **1** 份异地备份

### 2. 定期验证

- 启用 `auto_verify` 选项
- 每周执行一次恢复演练
- 监控备份成功率

### 3. 监控和告警

- 配置失败通知
- 设置 Webhook 集成
- 定期检查备份大小趋势

### 4. 存储优化

- 使用增量备份减少存储
- 定期清理过期备份
- 压缩备份文件

## 🐛 故障排查

### 备份失败

检查日志:

```bash
tail -f logs/plugin_cloud_backup.log
```

常见问题:

1. 数据库连接失败 - 检查 DB_HOST/DB_PORT
2. 磁盘空间不足 - 清理旧备份
3. 云存储认证失败 - 检查 Access Key

### 恢复失败

1. 验证备份文件完整性
2. 检查目标数据库权限
3. 确认 PostgreSQL 版本兼容性

## 📈 性能指标

- 完整备份时间: ~5-10分钟 (取决于数据量)
- 增量备份时间: ~1-2分钟
- 文件备份时间: ~2-5分钟
- 备份验证时间: ~30秒

## 🔄 升级

从 v1.0 (backup-manager) 升级到 v2.0:

1. 备份现有配置
2. 停用旧插件
3. 激活新插件
4. 迁移备份历史 (可选)

## 🤝 贡献

欢迎提交 Issue 和 Pull Request!

## 📄 许可证

Apache License 2.0

---

**FastBlog Team** - 为您的博客提供可靠的数据保护
