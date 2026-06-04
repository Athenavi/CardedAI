@echo off
REM Meilisearch 快速启动脚本 (Windows版本)
REM 用于快速部署和配置 Meilisearch 搜索引擎

echo ==========================================
echo   FastBlog Meilisearch 快速启动
echo ==========================================
echo.

REM 检查 Docker 是否安装
where docker >nul 2>nul
if %errorlevel% neq 0 (
    echo ❌ Docker 未安装，请先安装 Docker Desktop
    pause
    exit /b 1
)

REM 检查 Docker Compose 是否安装
where docker-compose >nul 2>nul
if %errorlevel% neq 0 (
    docker compose version >nul 2>nul
    if %errorlevel% neq 0 (
        echo ❌ Docker Compose 未安装，请先安装 Docker Desktop
        pause
        exit /b 1
    )
    set DOCKER_COMPOSE=docker compose
) else (
    set DOCKER_COMPOSE=docker-compose
)

echo ✅ Docker 和 Docker Compose 已安装
echo.

REM 创建数据目录
echo 📁 创建数据目录...
if not exist "meili_data" mkdir meili_data
echo ✅ 数据目录已创建
echo.

REM 启动 Meilisearch
echo 🚀 启动 Meilisearch...
%DOCKER_COMPOSE% -f docker-compose.meilisearch.yml up -d

echo.
echo ⏳ 等待 Meilisearch 启动...
timeout /t 5 /nobreak >nul

REM 检查服务状态
%DOCKER_COMPOSE% -f docker-compose.meilisearch.yml ps | findstr "Up" >nul
if %errorlevel% equ 0 (
    echo ✅ Meilisearch 已成功启动！
    echo.
    echo 📊 服务信息:
    echo    - 地址: http://localhost:7700
    echo    - 健康检查: http://localhost:7700/health
    echo.
    echo 🔧 下一步操作:
    echo    1. 在 FastBlog 后台激活'全文搜索引擎'插件
    echo    2. 配置插件设置（服务器地址: http://localhost:7700）
    echo    3. 执行索引重建以导入现有文章
    echo.
    echo 📝 常用命令:
    echo    - 查看日志: %DOCKER_COMPOSE% -f docker-compose.meilisearch.yml logs -f
    echo    - 停止服务: %DOCKER_COMPOSE% -f docker-compose.meilisearch.yml down
    echo    - 重启服务: %DOCKER_COMPOSE% -f docker-compose.meilisearch.yml restart
    echo.
) else (
    echo ❌ Meilisearch 启动失败，请检查日志:
    %DOCKER_COMPOSE% -f docker-compose.meilisearch.yml logs
    pause
    exit /b 1
)

pause
