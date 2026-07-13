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

function Write-Info  { Write-Host "[INFO]  $args" -ForegroundColor Cyan }
function Write-Ok    { Write-Host "[OK]    $args" -ForegroundColor Green }
function Write-Warn  { Write-Host "[WARN]  $args" -ForegroundColor Yellow }
function Write-Err   { Write-Host "[ERROR] $args" -ForegroundColor Red }

# ==== 1. 检测 Python ====
Write-Info "Check Python..."
$PythonPath = $null
foreach ($cmd in @("python3", "python")) {
    try {
        $ver = & $cmd --version 2>&1
        if ($ver -match "(\d+)\.(\d+)") {
            if ([int]$Matches[1] -ge 3 -and [int]$Matches[2] -ge 11) {
                $PythonPath = (Get-Command $cmd -ErrorAction SilentlyContinue).Source
                break
            }
        }
    } catch { }
}
if (-not $PythonPath) { Write-Err "Need Python >= 3.11"; exit 1 }
Write-Ok "$(& $PythonPath --version 2>&1)"

# ==== 2. 虚拟环境 ====
$VenvDir = Join-Path $ProjectDir ".venv"
if (-not (Test-Path $VenvDir)) {
    Write-Info "Creating venv..."
    & $PythonPath -m venv $VenvDir
    Write-Ok "venv created: $VenvDir"
} else { Write-Ok "venv exists" }

$VenvPython = Join-Path $VenvDir "Scripts\python.exe"
if (-not (Test-Path $VenvPython)) { Write-Err "venv python not found"; exit 1 }

# ==== 3. 安装依赖 ====
Write-Info "Installing deps..."
& $VenvPython -m pip install -q --upgrade pip
& $VenvPython -m pip install -q -r requirements.txt
if ($LASTEXITCODE -ne 0) { Write-Err "pip install failed"; exit 1 }
Write-Ok "deps installed"

# ==== 4. 创建 .env（SQLite）====
$EnvFile = Join-Path $ProjectDir ".env"
if (-not (Test-Path $EnvFile)) {
    Write-Info "Creating .env (SQLite)..."
    $SecretKey = & $VenvPython -c "import secrets; print(secrets.token_hex(32))"
    @"
# CardedAI - SQLite config (auto-generated)
DB_ENGINE=sqlite
DB_PATH=data/cardedai.db
DOMAIN=http://localhost:9421
TITLE=CardedAI
SECRET_KEY=$SecretKey
TIME_ZONE=Asia/Shanghai
ENVIRONMENT=development
DEBUG=True
JWT_EXPIRATION_DELTA=86400
REFRESH_TOKEN_EXPIRATION_DELTA=64800
CACHE_TYPE=simple
"@ | Out-File -FilePath $EnvFile -Encoding utf8
    Write-Ok ".env created"
} else { Write-Ok ".env exists" }

# ==== 5. 确保 data 目录 ====
$DataDir = Join-Path $ProjectDir "data"
New-Item -ItemType Directory -Force -Path $DataDir | Out-Null

# ==== 6. 数据库迁移 ====
Write-Info "Running alembic migrations..."
& $VenvPython -m alembic upgrade head
if ($LASTEXITCODE -eq 0) { Write-Ok "migrations done" }
else { Write-Warn "migrations failed, trying auto-create tables..."
$pythonCode = @"
from src.utils.database.unified_manager import db_manager
db_manager.initialize()
from src.extensions import _get_sync_session_factory
_session = _get_sync_session_factory()
print('Tables created')
"@
& $VenvPython -c $pythonCode 2>$null
if ($LASTEXITCODE -eq 0) { Write-Ok "tables created" }
else { Write-Warn "table creation skipped" } }

# ==== 7. 启动服务 ====
Write-Host ""
Write-Host "============================================" -ForegroundColor Green
Write-Host "  CardedAI starting..." -ForegroundColor Green
Write-Host "  http://localhost:9421" -ForegroundColor Green
Write-Host "  SQLite: $(Join-Path $ProjectDir 'data\cardedai.db')" -ForegroundColor Green
Write-Host "============================================" -ForegroundColor Green
Write-Host ""
& $VenvPython main.py --env dev --port 9421
