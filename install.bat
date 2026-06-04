@echo off
REM FastBlog 一键安装脚本 (Windows)
REM 需要预先安装Docker Desktop

echo =========================================
echo   FastBlog 一键安装脚本 (Windows)
echo =========================================
echo.

REM 检查Docker
where docker >nul 2>nul
if %errorlevel% neq 0 (
    echo [ERROR] Docker未安装
    echo 请先安装Docker Desktop: https://www.docker.com/products/docker-desktop
    pause
    exit /b 1
)

echo [OK] Docker已安装
docker --version
echo.

REM 检查Docker Compose
where docker-compose >nul 2>nul
if %errorlevel% neq 0 (
    echo [WARNING] docker-compose命令未找到，尝试使用docker compose...
    docker compose version >nul 2>nul
    if %errorlevel% neq 0 (
        echo [ERROR] Docker Compose未安装
        pause
        exit /b 1
    )
    set COMPOSE_CMD=docker compose
) else (
    set COMPOSE_CMD=docker-compose
)

echo [OK] Docker Compose已安装
echo.

REM 创建.env文件
if not exist .env (
    echo [INFO] 创建.env配置文件...
    copy .env_example .env >nul
    
    REM 生成随机密钥（简化版）
    echo SECRET_KEY=%RANDOM%%RANDOM%%RANDOM%%RANDOM% >> .env
    
    echo [OK] .env文件创建完成
) else (
    echo [OK] .env文件已存在
)
echo.

REM 创建必要目录
echo [INFO] 创建必要目录...
if not exist media mkdir media
if not exist upload_chunks mkdir upload_chunks
if not exist static mkdir static
if not exist themes mkdir themes
if not exist plugins mkdir plugins
if not exist translations mkdir translations
if not exist backups mkdir backups
if not exist logs mkdir logs
if not exist storage mkdir storage
if not exist nginx mkdir nginx
if not exist nginx\conf.d mkdir nginx\conf.d
if not exist ssl mkdir ssl
echo [OK] 目录创建完成
echo.

REM 启动服务
echo [INFO] 启动FastBlog服务...
%COMPOSE_CMD% up -d
if %errorlevel% neq 0 (
    echo [ERROR] 服务启动失败
    pause
    exit /b 1
)
echo [OK] 服务启动完成
echo.

REM 等待服务就绪
echo [INFO] 等待服务就绪...
timeout /t 10 /nobreak >nul

for /L %%i in (1,1,30) do (
    curl -s http://localhost:9421/api/v1/health >nul 2>&1
    if %errorlevel% equ 0 (
        echo [OK] FastBlog已就绪!
        goto :ready
    )
    echo -n .
    timeout /t 2 /nobreak >nul
)

echo [ERROR] 服务启动超时
pause
exit /b 1

:ready
echo.
echo =========================================
echo   FastBlog 安装完成!
echo =========================================
echo.
echo 访问地址: http://localhost:9421
echo.
echo 常用命令:
echo   查看日志: docker-compose logs -f app
echo   停止服务: docker-compose down
echo   重启服务: docker-compose restart
echo.
echo 配置文件: .env
echo 数据目录: .\media, .\storage, .\backups
echo.

pause
