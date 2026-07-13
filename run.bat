@echo off
REM ===========================================================================
REM CardedAI 一键启动脚本 (Windows CMD 双击版)
REM 默认使用 SQLite，无需 PostgreSQL / Redis 等外部依赖
REM 自动检测 Python、创建虚拟环境、安装依赖、启动服务
REM ===========================================================================

chcp 65001 >nul 2>&1
setlocal enabledelayedexpansion

title CardedAI - 一键启动

set "PROJECT_DIR=%~dp0"
cd /d "%PROJECT_DIR%"

echo [INFO]  检查 Python 环境...

REM ---------- 检测 Python ----------
set "PYTHON_CMD="
for %%c in (python python3) do (
    for /f "usebackq tokens=*" %%v in (`%%c --version 2^>nul`) do (
        echo %%v | findstr /R "3\.1[1-9] 3\.[2-9][0-9]" >nul 2>&1
        if !errorlevel! equ 0 (
            set "PYTHON_CMD=%%c"
            goto :found_python
        )
    )
)

REM Fallback: just check if Python exists
for %%c in (python python3) do (
    for /f "usebackq tokens=*" %%v in (`%%c --version 2^>nul`) do (
        set "PYTHON_CMD=%%c"
        goto :found_python
    )
)

echo [ERROR] 未找到 Python，请安装 Python ^>= 3.11
echo         下载地址: https://www.python.org/downloads/
pause
exit /b 1

:found_python
%PYTHON_CMD% --version
echo [OK]    Python 已找到

REM ---------- 创建虚拟环境 ----------
set "VENV_DIR=%PROJECT_DIR%.venv"
if not exist "%VENV_DIR%" (
    echo [INFO]  创建虚拟环境...
    %PYTHON_CMD% -m venv "%VENV_DIR%"
    if !errorlevel! neq 0 (
        echo [ERROR] 虚拟环境创建失败
        pause
        exit /b 1
    )
    echo [OK]    虚拟环境已创建
) else (
    echo [OK]    虚拟环境已存在
)

set "VENV_PYTHON=%VENV_DIR%\Scripts\python.exe"
if not exist "!VENV_PYTHON!" (
    echo [ERROR] 虚拟环境 Python 未找到: !VENV_PYTHON!
    pause
    exit /b 1
)

REM ---------- 安装依赖 ----------
echo [INFO]  安装/更新 Python 依赖...
"!VENV_PYTHON!" -m pip install -q --upgrade pip
"!VENV_PYTHON!" -m pip install -q -r requirements.txt
if !errorlevel! neq 0 (
    echo [ERROR] pip install 失败
    pause
    exit /b 1
)
echo [OK]    依赖安装完成

REM ---------- 创建 .env 文件 ----------
if not exist "%PROJECT_DIR%.env" (
    echo [INFO]  创建 .env 配置文件（SQLite 模式）...

    REM 生成随机 SECRET_KEY
    for /f "delims=" %%s in ('"!VENV_PYTHON!" -c "import secrets; print(secrets.token_hex(32))"') do set "SECRET_KEY=%%s"

    (
        echo # ============================================================================
        echo # CardedAI - SQLite 开发环境配置（由 run.bat 自动生成）
        echo # 如需要使用 PostgreSQL，请参考 .env.example 手动配置
        echo # ============================================================================
        echo.
        echo # Database - SQLite（无需外部数据库）
        echo DB_ENGINE=sqlite
        echo DB_PATH=data/cardedai.db
        echo.
        echo # Application
        echo DOMAIN=http://localhost:9421
        echo TITLE=CardedAI
        echo SECRET_KEY=%SECRET_KEY%
        echo TIME_ZONE=Asia/Shanghai
        echo ENVIRONMENT=development
        echo DEBUG=True
        echo.
        echo # JWT
        echo JWT_EXPIRATION_DELTA=86400
        echo REFRESH_TOKEN_EXPIRATION_DELTA=64800
        echo.
        echo # Caching（无 Redis 时自动降级为内存缓存）
        echo CACHE_TYPE=simple
    ) > "%PROJECT_DIR%.env"
    echo [OK]    .env 文件已创建（SQLite 模式）
) else (
    echo [OK]    .env 文件已存在，跳过创建
)

REM ---------- 确保 data 目录存在 ----------
if not exist "%PROJECT_DIR%data" mkdir "%PROJECT_DIR%data"

REM ---------- 运行数据库迁移 ----------
echo [INFO]  运行数据库迁移...
"!VENV_PYTHON!" -m alembic upgrade head 2>nul
if !errorlevel! equ 0 (
    echo [OK]    数据库迁移完成
) else (
    echo [WARN]  Alembic 迁移失败，尝试自动建表...
    "!VENV_PYTHON!" -c "from src.utils.database.unified_manager import db_manager; db_manager.initialize(); from src.extensions import _get_sync_session_factory; _session = _get_sync_session_factory(); print('Tables created successfully')" 2>nul
    if !errorlevel! equ 0 (
        echo [OK]    自动建表完成
    ) else (
        echo [WARN]  自动建表跳过，服务启动后会自动处理
    )
)

REM ---------- 启动服务 ----------
echo.
echo ============================================
echo   CardedAI 启动中...
echo   访问地址: http://localhost:9421
echo   数据库:   SQLite (%PROJECT_DIR%data\cardedai.db)
echo ============================================
echo.

"!VENV_PYTHON!" main.py --env dev --port 9421

pause
