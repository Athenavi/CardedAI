# FastBlog 进程监督器使用指南

## 📋 概述

FastBlog 进程监督器是一个强大的多进程管理系统，提供自动故障恢复、健康检查、集中监控等功能。

## 🚀 快速开始

### 1. 启动进程监督器

```bash
# 使用监督器模式启动主应用
python main.py --mode supervisor --env prod
```

### 2. （可选）启动 Web 管理界面

```bash
# 单独启动 Web 管理界面
python process_supervisor/start_web_admin.py
```

启动后访问：http://127.0.0.1:9422

## 📦 管理的进程

默认配置下，监督器管理以下进程：

| 进程名称            | 描述              | 端口   | 自动启动 |
|-----------------|-----------------|------|------|
| `main_app`      | FastAPI 主应用     | 9421 | ✅    |
| `django_server` | Django 管理服务     | 8000 | ✅    |
| `update_server` | 更新检查服务          | 8001 | ✅    |
| `frontend_dev`  | Next.js 前端开发服务器 | 3000 | ❌    |

## 🔧 配置文件

配置文件位于：`process_supervisor/supervisor_config.json`

### 添加新进程

```json
{
   "processes": {
      "your_service": {
         "command": [
            "python",
            "your_script.py"
         ],
         "working_dir": ".",
         "autostart": true,
         "autorestart": true,
         "restart_limit": 3,
         "restart_delay": 5,
         "stdout_logfile": "logs/your_service.log",
         "stderr_logfile": "logs/your_service.err.log",
         "health_check": {
            "endpoint": "http://127.0.0.1:8080/health",
            "interval": 30,
            "timeout": 5,
            "retries": 3
         }
      }
   }
}
```

### 配置参数说明

#### 进程配置

- `command`: 启动命令（数组格式）
- `working_dir`: 工作目录
- `autostart`: 是否自动启动
- `autorestart`: 是否自动重启
- `restart_limit`: 最大重启次数
- `restart_delay`: 重启延迟（秒）
- `restart_backoff_multiplier`: 重启延迟指数退避乘数
- `max_restart_delay`: 最大重启延迟
- `stdout_logfile`: 标准输出日志文件
- `stderr_logfile`: 错误日志文件
- `environment`: 环境变量

#### 健康检查配置

- `endpoint`: HTTP 健康检查端点
- `interval`: 检查间隔（秒）
- `timeout`: 超时时间（秒）
- `retries`: 重试次数

## 🎯 核心功能

### 1. 自动故障恢复

- 进程崩溃时自动重启
- 智能重启延迟（指数退避算法）
- 连续失败次数限制

### 2. 三层健康检查

**Layer 1**: 进程存活检查

- 检查进程是否在运行

**Layer 2**: 端口监听检查

- 自动从命令中提取端口
- 支持 IP:Port 格式

**Layer 3**: HTTP 端点检查

- 检查健康端点响应
- 支持状态码验证

### 3. 日志聚合

每 5 分钟自动聚合所有进程日志到：

- `logs/aggregated_system.log`

包含每个进程的最后 50 行日志

### 4. 实时监控

- CPU 使用率
- 内存使用率
- 进程运行时间
- 健康检查状态

## 🌐 Web 管理界面

### 功能特性

1. **实时仪表盘**
   - 系统整体状态概览
   - 进程运行统计
   - 健康状态监控

2. **进程管理**
   - 查看进程详细信息
   - 手动启停进程
   - 重启进程

3. **API 接口**

```bash
# 获取系统状态
GET /api/system/status

# 获取所有进程状态
GET /api/processes

# 获取指定进程状态
GET /api/process/{process_name}

# 启动进程
POST /api/process/{process_name}/start

# 停止进程
POST /api/process/{process_name}/stop

# 重启进程
POST /api/process/{process_name}/restart

# 健康检查
GET /api/health
```

### API 文档

访问 http://127.0.0.1:9422/docs 查看完整的 Swagger API 文档

## 📊 日志文件

| 日志文件                         | 描述             |
|------------------------------|----------------|
| `logs/supervisor.log`        | 监督器主日志         |
| `logs/main_app.log`          | 主应用日志          |
| `logs/django_server.log`     | Django 服务日志    |
| `logs/update_server.log`     | 更新服务日志         |
| `logs/frontend_dev.log`      | 前端开发日志         |
| `logs/aggregated_system.log` | 聚合日志（每 5 分钟更新） |

## 🔍 监控和维护

### 查看进程状态

```python
from process_supervisor.process_manager import get_supervisor

supervisor = get_supervisor()

# 获取所有进程状态
statuses = supervisor.get_all_status()

# 获取指定进程状态
status = supervisor.get_process_status("main_app")
print(status)
```

### 手动控制进程

```python
# 启动进程
supervisor.start_process("main_app")

# 停止进程
supervisor.stop_process("main_app")

# 重启进程
supervisor.restart_process("main_app")
```

## ⚙️ 高级模式

### 开发模式

仅启动必要的服务：

```json
{
   "processes": {
      "frontend_dev": {
         "autostart": true
      }
   }
}
```

### 生产模式

禁用开发相关服务：

```json
{
   "processes": {
      "frontend_dev": {
         "autostart": false
      }
   }
}
```

## 🐛 故障排查

### 进程无法启动

1. 检查日志文件查看详细错误
2. 验证命令和工作目录是否正确
3. 确认端口未被占用
4. 检查环境变量配置

### 健康检查失败

1. 确认服务确实在运行
2. 检查健康端点 URL 是否正确
3. 验证端口配置
4. 增加超时时间或重试次数

### 日志不输出

1. 检查日志文件路径权限
2. 确认日志级别设置
3. 验证日志目录是否存在

## 📝 最佳实践

1. **合理设置重启限制**
   - 生产环境：3-5 次
   - 开发环境：5-10 次

2. **配置健康检查**
   - 关键服务必须配置
   - 间隔时间建议 30-60 秒
   - 超时时间建议 3-5 秒

3. **日志管理**
   - 定期清理旧日志
   - 使用日志轮转
   - 聚合日志便于排查

4. **资源监控**
   - 关注 CPU 和内存使用
   - 设置合理的资源限制
   - 定期检查性能瓶颈

## 🔄 更新配置

修改配置文件后无需重启监督器：

1. 编辑 `supervisor_config.json`
2. 监督器会自动检测配置变化
3. 下次启动时应用新配置

或者手动触发重新加载：

```python
from process_supervisor.config_manager import get_config_manager

config_manager = get_config_manager()
config_manager.reload_config()
```

## 💡 提示

- 使用 Web 管理界面可以直观地查看所有进程状态
- 聚合日志文件是排查问题的首选位置
- 健康检查连续失败 3 次会触发重启
- 进程重启后有 5 秒稳定期确保服务正常

## 🆘 需要帮助？

遇到问题时：

1. 查看 `logs/supervisor.log` 了解监督器状态
2. 查看对应进程的日志文件
3. 检查 `logs/aggregated_system.log` 获取全局视图
4. 使用 Web 管理界面的 API 诊断问题
