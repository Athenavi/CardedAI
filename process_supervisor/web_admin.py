#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
进程监督器 Web 管理界面 API
提供 RESTful API 用于监控和管理进程
"""

from typing import Dict, Optional

try:
    from fastapi import FastAPI, HTTPException
    from fastapi.responses import HTMLResponse, JSONResponse
    from pydantic import BaseModel

    HAS_FASTAPI = True
except ImportError:
    HAS_FASTAPI = False
    logging.warning("FastAPI 未安装，Web 管理界面将不可用")

# 创建 FastAPI 应用
if HAS_FASTAPI:
    app = FastAPI(
        title="FastBlog 进程监督器管理界面",
        description="提供进程监控、管理和健康检查的 RESTful API",
        version="1.0.0"
    )
else:
    app = None


# 数据模型
class ProcessStatusModel(BaseModel):
    """进程状态模型"""
    name: str
    status: str
    pid: Optional[int] = None
    uptime: float = 0
    uptime_formatted: str = "0s"
    restart_count: int = 0
    cpu_percent: Optional[float] = None
    memory_mb: Optional[float] = None
    health_check_failures: int = 0


class SystemStatusModel(BaseModel):
    """系统状态模型"""
    total_processes: int
    running_processes: int
    healthy_processes: int
    processes: Dict[str, ProcessStatusModel]


# 重建模型以解决前向引用问题
ProcessStatusModel.model_rebuild()
SystemStatusModel.model_rebuild()


# 全局监督器引用
_supervisor = None


def set_supervisor(supervisor):
    """设置监督器实例"""
    global _supervisor
    _supervisor = supervisor


def get_supervisor():
    """获取监督器实例"""
    return _supervisor


if HAS_FASTAPI and app:

    @app.get("/", response_class=HTMLResponse, tags=["Web 界面"])
    async def root():
        """返回管理界面 HTML"""
        html_content = """
<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>FastBlog 进程监督器</title>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body {
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
            padding: 20px;
        }
        .container {
            max-width: 1200px;
            margin: 0 auto;
            background: white;
            border-radius: 15px;
            box-shadow: 0 10px 40px rgba(0,0,0,0.2);
            overflow: hidden;
        }
        .header {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 30px;
            text-align: center;
        }
        .header h1 { font-size: 2.5em; margin-bottom: 10px; }
        .header p { opacity: 0.9; }
        .content { padding: 30px; }
        .stats-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
            gap: 20px;
            margin-bottom: 30px;
        }
        .stat-card {
            background: #f8f9fa;
            border-radius: 10px;
            padding: 20px;
            text-align: center;
            transition: transform 0.3s;
        }
        .stat-card:hover { transform: translateY(-5px); }
        .stat-number {
            font-size: 2.5em;
            font-weight: bold;
            color: #667eea;
        }
        .stat-label { color: #666; margin-top: 10px; }
        .process-list { margin-top: 20px; }
        .process-item {
            background: #fff;
            border: 1px solid #e0e0e0;
            border-radius: 8px;
            padding: 15px;
            margin-bottom: 15px;
            display: flex;
            justify-content: space-between;
            align-items: center;
            transition: all 0.3s;
        }
        .process-item:hover {
            box-shadow: 0 5px 15px rgba(0,0,0,0.1);
            border-color: #667eea;
        }
        .process-info h3 { color: #333; margin-bottom: 5px; }
        .process-details { color: #666; font-size: 0.9em; }
        .status-badge {
            padding: 6px 15px;
            border-radius: 20px;
            font-weight: bold;
            font-size: 0.85em;
        }
        .status-running {
            background: #d4edda;
            color: #155724;
        }
        .status-stopped, .status-failed {
            background: #f8d7da;
            color: #721c24;
        }
        .status-restarting {
            background: #fff3cd;
            color: #856404;
        }
        .refresh-btn {
            background: #667eea;
            color: white;
            border: none;
            padding: 12px 30px;
            border-radius: 8px;
            cursor: pointer;
            font-size: 1em;
            transition: background 0.3s;
        }
        .refresh-btn:hover { background: #5568d3; }
        .loading { text-align: center; padding: 40px; color: #666; }
        .error { color: #dc3545; padding: 20px; text-align: center; }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🚀 FastBlog 进程监督器</h1>
            <p>实时监控系统进程状态</p>
        </div>
        <div class="content">
            <div style="text-align: right; margin-bottom: 20px;">
                <button class="refresh-btn" onclick="loadData()">🔄 刷新状态</button>
            </div>
            
            <div id="stats" class="stats-grid">
                <div class="loading">正在加载统计数据...</div>
            </div>
            
            <h2 style="margin-bottom: 15px;">进程列表</h2>
            <div id="processes" class="process-list">
                <div class="loading">正在加载进程列表...</div>
            </div>
        </div>
    </div>
    
    <script>
        async function loadData() {
            try {
                const [statsRes, processesRes] = await Promise.all([
                    fetch('/api/system/status'),
                    fetch('/api/processes')
                ]);
                
                if (!statsRes.ok || !processesRes.ok) {
                    throw new Error('API 请求失败');
                }
                
                const stats = await statsRes.json();
                const processes = await processesRes.json();
                
                // 更新统计卡片
                document.getElementById('stats').innerHTML = `
                    <div class="stat-card">
                        <div class="stat-number">${stats.total_processes !== null ? stats.total_processes : 0}</div>
                        <div class="stat-label">总进程数</div>
                    </div>
                    <div class="stat-card">
                        <div class="stat-number">${stats.running_processes !== null ? stats.running_processes : 0}</div>
                        <div class="stat-label">运行中</div>
                    </div>
                    <div class="stat-card">
                        <div class="stat-number">${stats.healthy_processes !== null ? stats.healthy_processes : 0}</div>
                        <div class="stat-label">健康</div>
                    </div>
                `;
                
                // 更新进程列表
                const processList = document.getElementById('processes');
                if (Object.keys(processes).length === 0) {
                    processList.innerHTML = '<div class="loading">暂无进程</div>';
                    return;
                }
                
                processList.innerHTML = Object.entries(processes).map(([name, info]) => `
                    <div class="process-item">
                        <div class="process-info">
                            <h3>${name}</h3>
                            <div class="process-details">
                                PID: ${(info.pid !== null && info.pid !== undefined) ? info.pid : 'N/A'} | 
                                运行时间：${info.uptime_formatted || '0s'} | 
                                重启次数：${info.restart_count || 0}
                                ${info.cpu_percent !== null && info.cpu_percent !== undefined ? ` | CPU: ${info.cpu_percent}%` : ''}${info.memory_mb !== null && info.memory_mb !== undefined ? ` | 内存：${info.memory_mb}MB` : ''}
                                ${info.health_check_failures > 0 ? ` | ⚠ 健康检查失败：${info.health_check_failures}` : ''}
                            </div>
                        </div>
                        <span class="status-badge status-${info.status}">${info.status}</span>
                    </div>
                `).join('');
                
            } catch (error) {
                console.error('加载数据失败:', error);
                document.getElementById('stats').innerHTML = 
                    '<div class="error">加载数据失败：' + error.message + '</div>';
                document.getElementById('processes').innerHTML = '';
            }
        }
        
        // 页面加载时获取数据
        loadData();
        
        // 每 5 秒自动刷新
        setInterval(loadData, 5000);
    </script>
</body>
</html>
"""
        return html_content


    @app.get("/api/system/status", response_model=SystemStatusModel, tags=["系统监控"])
    async def get_system_status():
        """获取系统整体状态"""
        supervisor = get_supervisor()
        if not supervisor:
            raise HTTPException(status_code=503, detail="监督器未初始化")

        statuses = supervisor.get_all_status()
        total = len(statuses)
        running = sum(1 for s in statuses.values() if s['status'] == 'running')
        healthy = sum(1 for s in statuses.values()
                      if s['status'] == 'running' and s.get('health_check_failures', 0) == 0)

        return SystemStatusModel(
            total_processes=total,
            running_processes=running,
            healthy_processes=healthy,
            processes=statuses
        )


    @app.get("/api/processes", tags=["进程管理"])
    async def get_all_processes():
        """获取所有进程状态"""
        supervisor = get_supervisor()
        if not supervisor:
            raise HTTPException(status_code=503, detail="监督器未初始化")

        return supervisor.get_all_status()


    @app.get("/api/process/{process_name}", tags=["进程管理"])
    async def get_process(process_name: str):
        """获取指定进程状态"""
        supervisor = get_supervisor()
        if not supervisor:
            raise HTTPException(status_code=503, detail="监督器未初始化")

        status = supervisor.get_process_status(process_name)
        if not status:
            raise HTTPException(status_code=404, detail=f"进程 {process_name} 不存在")

        return status


    @app.post("/api/process/{process_name}/start", tags=["进程管理"])
    async def start_process(process_name: str):
        """启动指定进程"""
        supervisor = get_supervisor()
        if not supervisor:
            raise HTTPException(status_code=503, detail="监督器未初始化")

        success = supervisor.start_process(process_name)
        if not success:
            raise HTTPException(status_code=500, detail=f"启动进程 {process_name} 失败")

        return {"status": "success", "message": f"进程 {process_name} 已启动"}


    @app.post("/api/process/{process_name}/stop", tags=["进程管理"])
    async def stop_process(process_name: str):
        """停止指定进程"""
        supervisor = get_supervisor()
        if not supervisor:
            raise HTTPException(status_code=503, detail="监督器未初始化")

        success = supervisor.stop_process(process_name)
        if not success:
            raise HTTPException(status_code=500, detail=f"停止进程 {process_name} 失败")

        return {"status": "success", "message": f"进程 {process_name} 已停止"}


    @app.post("/api/process/{process_name}/restart", tags=["进程管理"])
    async def restart_process(process_name: str):
        """重启指定进程"""
        supervisor = get_supervisor()
        if not supervisor:
            raise HTTPException(status_code=503, detail="监督器未初始化")

        success = supervisor.restart_process(process_name)
        if not success:
            raise HTTPException(status_code=500, detail=f"重启进程 {process_name} 失败")

        return {"status": "success", "message": f"进程 {process_name} 已重启"}


    @app.get("/api/health", tags=["健康检查"])
    async def health_check():
        """监督器自身健康检查"""
        supervisor = get_supervisor()
        if not supervisor:
            return {"status": "unhealthy", "message": "监督器未初始化"}

        if not supervisor.running:
            return {"status": "unhealthy", "message": "监督器未运行"}

        return {"status": "healthy", "message": "监督器运行正常"}
