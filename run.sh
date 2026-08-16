#!/usr/bin/env bash
# ============================================================================
# CardedAI 一键启动脚本 (Linux / macOS)
# 默认使用 SQLite，无需 PostgreSQL / Redis 等外部依赖
# ============================================================================

set -e

# ---------- 颜色输出 ----------
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

info()  { echo -e "${CYAN}[INFO]${NC}  $1"; }
ok()    { echo -e "${GREEN}[OK]${NC}    $1"; }
warn()  { echo -e "${YELLOW}[WARN]${NC}  $1"; }
err()   { echo -e "${RED}[ERROR]${NC} $1"; }

# ---------- 项目根目录 ----------
PROJECT_DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$PROJECT_DIR"

# ---------- 1. 检测 Python ----------
info "检查 Python 环境..."

PYTHON=""
for cmd in python3 python; do
    if command -v "$cmd" &>/dev/null; then
        PY_VER=$("$cmd" --version 2>&1 | grep -oP '\d+\.\d+')
        PY_MAJOR=$(echo "$PY_VER" | cut -d. -f1)
        PY_MINOR=$(echo "$PY_VER" | cut -d. -f2)
        if [ "$PY_MAJOR" -ge 3 ] && [ "$PY_MINOR" -ge 11 ]; then
            PYTHON="$cmd"
            break
        fi
    fi
done

if [ -z "$PYTHON" ]; then
    err "需要 Python >= 3.11，请安装后重试"
    exit 1
fi
ok "Python: $($PYTHON --version)"

# ---------- 2. 创建虚拟环境 ----------
VENV_DIR="$PROJECT_DIR/.venv"
if [ ! -d "$VENV_DIR" ]; then
    info "创建虚拟环境..."
    "$PYTHON" -m venv "$VENV_DIR"
    ok "虚拟环境已创建: $VENV_DIR"
else
    ok "虚拟环境已存在"
fi

# 激活虚拟环境
source "$VENV_DIR/bin/activate"

# ---------- 3. 安装依赖 ----------
info "安装/更新 Python 依赖..."
pip install -q --upgrade pip
pip install -q -r requirements.txt
ok "依赖安装完成"

# ---------- 4. 创建 .env 文件（环境检测推荐 + SQLite 本地降级） ----------
if [ ! -f "$PROJECT_DIR/.env" ]; then
    info "检测本机运行环境并生成推荐配置..."

    # 生成随机 SECRET_KEY
    SECRET_KEY=$("$PYTHON" -c "import secrets; print(secrets.token_hex(32))")

    # 环境检测：检测 PostgreSQL/Redis/Milvus/Qdrant/Meilisearch 是否可用并给出推荐
    # （纯标准库实现，零依赖；推荐仅用于首次生成 .env，已存在的配置不会被覆盖）
    RECOMMEND=$("$PYTHON" "$PROJECT_DIR/src/utils/environment_detector.py" --recommend 2>/dev/null) || RECOMMEND=""

    cat > "$PROJECT_DIR/.env" << EOF
# ============================================================================
# CardedAI - 零外部服务配置（由 run.sh 自动生成）
# 已根据本机环境自动推荐最优配置（见下方"环境自动检测推荐配置"段）
# 如需手动调整，直接修改对应键值后重启即可
# 如检测到本机有 PostgreSQL/Redis/Milvus/Qdrant/Meilisearch，将自动优先使用；
# 未检测到则全部使用内置本地方案（SQLite + 内存缓存 + 本地向量 + 内置搜索）
# ============================================================================

# Application
DOMAIN=http://localhost:9421
TITLE=CardedAI
SECRET_KEY=$SECRET_KEY
TIME_ZONE=Asia/Shanghai
ENVIRONMENT=development
DEBUG=True

# JWT
JWT_EXPIRATION_DELTA=86400
REFRESH_TOKEN_EXPIRATION_DELTA=64800

$RECOMMEND
EOF
    ok ".env 文件已创建（环境检测推荐配置）"
else
    ok ".env 文件已存在，跳过生成（如需重新检测推荐，删除 .env 后重跑）"
fi

# ---------- 5. 确保 data 目录存在 ----------
mkdir -p "$PROJECT_DIR/data"

# ---------- 6. 运行数据库迁移 ----------
info "运行数据库迁移..."
"$PYTHON" -m alembic upgrade head 2>/dev/null && {
    ok "数据库迁移完成"
} || {
    warn "Alembic 迁移失败，尝试自动建表..."
    # 如果 alembic 迁移失败（如首次运行没有基线），尝试直接建表
    "$PYTHON" -c "
from src.utils.database.unified_manager import db_manager
db_manager.initialize()
from src.extensions import _get_sync_session_factory
_session = _get_sync_session_factory()
print('Tables created successfully')
" 2>/dev/null || warn "自动建表跳过，服务启动后会自动处理"
}

# ---------- 7. 配置摘要 ----------
echo ""
info "当前生效配置："
grep -E "^(DB_ENGINE|DB_PATH|CACHE_TYPE|VECTOR_DB_TYPE|MEILISEARCH_HOST|EMBEDDING_PROVIDER)=" "$PROJECT_DIR/.env" 2>/dev/null | sed 's/^/  /' || echo "  （.env 中未找到，使用默认值）"
echo ""

# ---------- 8. 启动服务 ----------
echo ""
echo -e "${GREEN}============================================${NC}"
echo -e "${GREEN}  CardedAI 启动中...${NC}"
echo -e "${GREEN}  访问地址: http://localhost:9421${NC}"
echo -e "${GREEN}  数据库:   SQLite ($PROJECT_DIR/data/cardedai.db)${NC}"
echo -e "${GREEN}============================================${NC}"
echo ""

# 启动 FastAPI 服务
exec "$PYTHON" main.py --env dev --port 9421
