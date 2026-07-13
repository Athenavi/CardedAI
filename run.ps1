<#
.SYNOPSIS
    CardedAI 一键启动脚本 (Windows PowerShell)
    默认使用 SQLite，无需 PostgreSQL / Redis 等外部依赖
.DESCRIPTION
    自动创建虚拟环境、安装依赖、配置 SQLite 环境变量、运行迁移、启动服务
#>

#Requires -Version 5.1

$ErrorActionPreference = "Stop"
$ProjectDir = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $ProjectDir

# ---------- 颜色输出函数 ----------
function Write-Info  { Write-Host "[INFO]  $args" -ForegroundColor Cyan }
function Write-Ok    { Write-Host "[OK]    $args" -ForegroundColor Green }
function Write-Warn  { Write-Host "[WARN]  $args" -ForegroundColor Yellow }
function Write-Err   { Write-Host "[ERROR] $args" -ForegroundColor Red }

# ---------- 1. 检测 Python ----------
Write-Info "检查 Python 环境..."

$PythonPath = $null
$pythonCandidates = @("python3", "python")
foreach ($cmd in $pythonCandidates) {
    try {
        $ver = & $cmd --version 2>&1
        if ($ver -match "(\d+)\.(\d+)") {
            $major = [int]$Matches[1]
            $minor = [int]$Matches[2]
            if ($major -ge 3 -and $minor -ge 11) {
                $PythonPath = (Get-Command $cmd -ErrorAction SilentlyContinue).Source
                break
            }
        }
    } catch { continue }
}

if (-not $PythonPath) {
    Write-Err "需要 Python >= 3.11，请安装后重试"
    exit 1
}
Write-Ok "Python: $(& $PythonPath --version 2>&1)"

# ---------- 2. 创建虚拟环境 ----------
$VenvDir = Join-Path $ProjectDir ".venv"
if (-not (Test-Path $VenvDir)) {
    Write-Info "创建虚拟环境..."
    & $PythonPath -m venv $VenvDir
    Write-Ok "虚拟环境已创建: $VenvDir"
} else {
    Write-Ok "虚拟环境已存在"
}

# 激活虚拟环境 (Windows)
$VenvPython = Join-Path $VenvDir "Scripts\python.exe"
if (-not (Test-Path $VenvPython)) {
    Write-Err "虚拟环境 Python 未找到: $VenvPython"
    exit 1
}

# ---------- 3. 安装依赖 ----------
Write-Info "安装/更新 Python 依赖..."
& $VenvPython -m pip install -q --upgrade pip
& $VenvPython -m pip install -q -r requirements.txt
if ($LASTEXITCODE -ne 0) {
    Write-Err "pip install 失败"
    exit 1
}
Write-Ok "依赖安装完成"

# ---------- 4. 创建 .env 文件（SQLite 模式） ----------
$EnvFile = Join-Path $ProjectDir ".env"
if (-not (Test-Path $EnvFile)) {
    Write-Info "创建 .env 配置文件（SQLite 模式）..."

    # 生成随机 SECRET_KEY
    $SecretKey = & $VenvPython -c "import secrets; print(secrets.token_hex(32))"

    @"
# ============================================================================
# CardedAI - SQLite 开发环境配置（由 run.ps1 自动生成）
# 如需要使用 PostgreSQL，请参考 .env.example 手动配置
# ============================================================================

# Database - SQLite（无需外部数据库）
DB_ENGINE=sqlite
DB_PATH=data/cardedai.db

# Application
DOMAIN=http://localhost:9421
TITLE=CardedAI
SECRET_KEY=$SecretKey
TIME_ZONE=Asia/Shanghai
ENVIRONMENT=development
DEBUG=True

# JWT
JWT_EXPIRATION_DELTA=86400
REFRESH_TOKEN_EXPIRATION_DELTA=64800

# Caching（无 Redis 时自动降级为内存缓存）
CACHE_TYPE=simple
"@ | Out-File -FilePath $EnvFile -Encoding utf8
    Write-Ok ".env 文件已创建（SQLite 模式）"
} else {
    Write-Ok ".env 文件已存在，跳过创建"
}

# ---------- 5. 确保 data 目录存在 ----------
$DataDir = Join-Path $ProjectDir "data"
New-Item -ItemType Directory -Force -Path $DataDir | Out-Null

# ---------- 6. 运行数据库迁移 ----------
Write-Info "运行数据库迁移..."
& $VenvPython -m alembic upgrade head 2>$null
if ($LASTEXITCODE -eq 0) {
    Write-Ok "数据库迁移完成"
} else {
    Write-Warn "Alembic 迁移失败，尝试自动建表..."
    # 如果 alembic 迁移失败，尝试直接建表
    & $VenvPython -c @"
from src.utils.database.unified_manager import db_manager
db_manager.initialize()
from src.extensions import _get_sync_session_factory
_session = _get_sync_session_factory()
print('Tables created successfully')
"@ 2>$null
    if ($LASTEXITCODE -eq 0) {
        Write-Ok "自动建表完成"
    } else {
        Write-Warn "自动建表跳过，服务启动后会自动处理"
    }
}

# ---------- 7. 启动服务 ----------
Write-Host ""
Write-Host "============================================" -ForegroundColor Green
Write-Host "  CardedAI 启动中..." -ForegroundColor Green
Write-Host "  访问地址: http://localhost:9421" -ForegroundColor Green
$dbPath = Join-Path $ProjectDir "data\cardedai.db"
Write-Host "  数据库:   SQLite ($dbPath)" -ForegroundColor Green
Write-Host "============================================" -ForegroundColor Green
Write-Host ""

# 启动 FastAPI 服务
& $VenvPython main.py --env dev --port 9421
