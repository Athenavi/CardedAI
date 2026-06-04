# FastBlog Cloud SSL Plugin

SSL证书自动管理插件,基于 Let's Encrypt 提供免费的 HTTPS 证书服务。

## ✨ 核心功能

### 1. Let's Encrypt 集成

- 免费 SSL/TLS 证书
- 自动化申请流程
- 支持生产和测试环境

### 2. 多种验证方式

- **HTTP-01**: 通过文件验证域名所有权
- **DNS-01**: 通过 DNS 记录验证 (支持通配符证书)
- 支持主流 DNS 提供商 (Cloudflare/阿里云/腾讯云)

### 3. 自动续期

- 定期检查证书有效期
- 到期前自动续期 (默认30天)
- 续期失败告警

### 4. Web 服务器集成

- Nginx 自动配置和部署
- Apache 支持 (计划中)
- 配置测试和安全重载

### 5. 证书监控

- 每日检查证书状态
- 多级告警 (30/14/7/1天)
- 过期紧急告警

### 6. 安全优化

- HSTS (HTTP Strict Transport Security)
- OCSP Stapling
- TLS 版本控制
- 加密套件优化

## 📦 安装

### 系统要求

```bash
# 安装 certbot
sudo apt-get install certbot python3-certbot-nginx  # Debian/Ubuntu
sudo yum install certbot python3-certbot-nginx      # CentOS/RHEL

# 或使用 snap
sudo snap install --classic certbot
```

### Python 依赖

```bash
# DNS 插件 (如果使用 DNS-01 验证)
pip install certbot-dns-cloudflare
pip install certbot-dns-aliyun
pip install certbot-dns-tencentcloud
```

## ⚙️ 配置

### 基础配置

```json
{
  "enabled": true,
  "acme": {
    "email": "admin@example.com",
    "server": "production",
    "agree_tos": true
  },
  "validation": {
    "method": "http-01"
  },
  "web_server": {
    "type": "nginx",
    "config_dir": "/etc/nginx",
    "reload_command": "systemctl reload nginx",
    "test_command": "nginx -t"
  }
}
```

### HTTP-01 验证配置

确保 Web 根目录可访问:

```json
{
  "validation": {
    "method": "http-01"
  },
  "webroot_path": "/var/www/html"
}
```

### DNS-01 验证配置 (Cloudflare)

1. 创建 Cloudflare API Token
2. 创建凭证文件 `/etc/letsencrypt/cloudflare-credentials.ini`:

```ini
dns_cloudflare_api_token = YOUR_API_TOKEN
```

3. 配置插件:

```json
{
  "validation": {
    "method": "dns-01",
    "dns_provider": "cloudflare"
  }
}
```

## 🚀 使用

### 申请证书

```bash
curl -X POST http://localhost:9421/api/v2/cloud/ssl/request \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "domain": "example.com",
    "email": "admin@example.com",
    "validation_method": "http-01",
    "wildcard": false
  }'
```

### 申请通配符证书

```bash
curl -X POST http://localhost:9421/api/v2/cloud/ssl/request \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "domain": "example.com",
    "validation_method": "dns-01",
    "wildcard": true
  }'
```

### 申请多域名证书 (SAN)

```bash
curl -X POST http://localhost:9421/api/v2/cloud/ssl/request \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "domain": "example.com",
    "additional_domains": ["www.example.com", "blog.example.com"],
    "validation_method": "http-01"
  }'
```

### 手动续期证书

```bash
curl -X POST http://localhost:9421/api/v2/cloud/ssl/renew/example.com \
  -H "Authorization: Bearer YOUR_TOKEN"
```

### 查看证书状态

```bash
curl -X GET http://localhost:9421/api/v2/cloud/ssl/status/example.com \
  -H "Authorization: Bearer YOUR_TOKEN"
```

响应示例:

```json
{
  "success": true,
  "domain": "example.com",
  "valid_from": "Jan  1 00:00:00 2024 GMT",
  "valid_until": "Apr  1 00:00:00 2024 GMT",
  "days_until_expiry": 45,
  "needs_renewal": false,
  "status": "active"
}
```

### 列出所有证书

```bash
curl -X GET http://localhost:9421/api/v2/cloud/ssl/list \
  -H "Authorization: Bearer YOUR_TOKEN"
```

## 📊 API 端点

| 端点                                  | 方法   | 描述      |
|-------------------------------------|------|---------|
| `/api/v2/cloud/ssl/request`         | POST | 申请SSL证书 |
| `/api/v2/cloud/ssl/renew/{domain}`  | POST | 续期证书    |
| `/api/v2/cloud/ssl/status/{domain}` | GET  | 查询证书状态  |
| `/api/v2/cloud/ssl/list`            | GET  | 列出所有证书  |
| `/api/v2/cloud/ssl/deploy/{domain}` | POST | 部署证书    |

## 🔧 Nginx 配置示例

### HTTP 重定向到 HTTPS

```nginx
server {
    listen 80;
    server_name example.com www.example.com;
    
    # Let's Encrypt 验证路径
    location /.well-known/acme-challenge/ {
        root /var/www/html;
    }
    
    # 其他请求重定向到 HTTPS
    location / {
        return 301 https://$server_name$request_uri;
    }
}
```

### HTTPS 服务器配置

```nginx
server {
    listen 443 ssl http2;
    server_name example.com www.example.com;
    
    # 证书路径
    ssl_certificate /etc/letsencrypt/live/example.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/example.com/privkey.pem;
    
    # SSL 优化
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers HIGH:!aNULL:!MD5;
    ssl_prefer_server_ciphers on;
    ssl_session_cache shared:SSL:10m;
    ssl_session_timeout 10m;
    
    # HSTS
    add_header Strict-Transport-Security "max-age=31536000" always;
    
    # OCSP Stapling
    ssl_stapling on;
    ssl_stapling_verify on;
    
    # 其他配置...
}
```

## 🔒 安全最佳实践

### 1. 证书管理

- ✅ 定期备份证书文件
- ✅ 使用强密码保护私钥
- ✅ 限制证书文件权限 (600)
- ✅ 监控证书过期时间

### 2. ACME 账户安全

- ✅ 使用专用邮箱注册
- ✅ 保管好账户密钥
- ✅ 定期更新联系方式

### 3. Web 服务器安全

- ✅ 禁用旧版 TLS (1.0/1.1)
- ✅ 使用强加密套件
- ✅ 启用 HSTS
- ✅ 配置 OCSP Stapling

### 4. DNS 凭证安全

```bash
# 设置正确的文件权限
sudo chmod 600 /etc/letsencrypt/cloudflare-credentials.ini
sudo chown root:root /etc/letsencrypt/cloudflare-credentials.ini
```

## 🐛 故障排查

### 证书申请失败

**问题**: "Failed authorization procedure"

**解决**:

1. 确认域名 DNS 解析正确
2. 检查防火墙是否允许 80/443 端口
3. 验证 Web 根目录可访问
4. 查看 certbot 日志: `/var/log/letsencrypt/letsencrypt.log`

### HTTP-01 验证失败

**问题**: "Invalid response from http://example.com/.well-known/acme-challenge/"

**解决**:

1. 确认 `.well-known` 目录存在且可写
2. 检查 Nginx/Apache 配置
3. 测试 URL 是否可从外部访问
4. 确认没有重定向规则干扰

### DNS-01 验证失败

**问题**: "DNS problem: NXDOMAIN"

**解决**:

1. 检查 DNS 凭证配置
2. 确认 API Token 权限正确
3. 等待 DNS 传播 (可能需要几分钟)
4. 检查 DNS 提供商 API 限流

### 证书未自动续期

**问题**: 证书过期但未自动续期

**解决**:

1. 检查 `auto_renewal.enabled` 是否为 true
2. 查看定时任务是否运行
3. 检查 certbot renew 日志
4. 手动执行续期测试: `certbot renew --dry-run`

## 📈 监控和告警

### 证书过期时间线

```
90天  → Let's Encrypt 证书有效期
30天  → 开始尝试自动续期
14天  → 发送警告通知
7天   → 发送严重警告
1天   → 发送紧急告警
0天   → 证书过期 (网站显示不安全)
```

### 告警渠道配置

```json
{
  "monitoring": {
    "notification_channels": ["email", "webhook"],
    "alert_before_days": [30, 14, 7, 1]
  }
}
```

## 🔄 证书轮换策略

### 蓝绿部署

1. 申请新证书
2. 测试新证书
3. 切换到新证书
4. 保留旧证书作为备份
5. 确认无误后删除旧证书

### 零停机更新

```bash
# 1. 续期证书
certbot renew

# 2. 测试配置
nginx -t

# 3. 平滑重载
systemctl reload nginx
```

## 🧪 测试环境

### 使用 Staging 服务器

```json
{
  "acme": {
    "server": "staging"
  }
}
```

**注意**: Staging 环境的证书不被浏览器信任,仅用于测试。

### 本地测试

```bash
# 生成自签名证书用于本地开发
openssl req -x509 -newkey rsa:4096 \
  -keyout key.pem -out cert.pem \
  -days 365 -nodes
```

## 📝 开发者指南

### 添加新的 DNS 提供商

1. 安装对应的 certbot DNS 插件
2. 创建凭证文件模板
3. 在插件中添加提供商配置
4. 更新文档

## 🤝 贡献

欢迎提交 Issue 和 Pull Request!

## 📄 许可证

Apache License 2.0

---

**FastBlog Team** - 让您的网站更安全
