#!/bin/bash
# FastBlog 自动备份脚本
# 用于定时备份数据库和文件

set -e

echo "========================================="
echo "  FastBlog 自动备份"
echo "========================================="
echo ""

# 配置
BACKUP_DIR="/backups"
DATABASE_BACKUP_DIR="$BACKUP_DIR/database"
FILES_BACKUP_DIR="$BACKUP_DIR/files"
RETENTION_DAYS=${BACKUP_RETENTION_DAYS:-30}
TIMESTAMP=$(date +%Y%m%d_%H%M%S)

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

# 创建备份目录
mkdir -p "$DATABASE_BACKUP_DIR" "$FILES_BACKUP_DIR"

echo -e "${YELLOW}开始备份...${NC}"
echo ""

# ==================== 数据库备份 ====================
echo -e "${YELLOW}[1/3] 备份数据库...${NC}"

DB_HOST=${DB_HOST:-postgres}
DB_PORT=${DB_PORT:-5432}
DB_NAME=${DB_NAME:-fastblog}
DB_USER=${DB_USER:-postgres}
DB_PASSWORD=${DB_PASSWORD:-}

export PGPASSWORD="$DB_PASSWORD"

BACKUP_FILE="$DATABASE_BACKUP_DIR/db_backup_${TIMESTAMP}.sql.gz"

if pg_dump -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" -d "$DB_NAME" | gzip > "$BACKUP_FILE"; then
    BACKUP_SIZE=$(du -h "$BACKUP_FILE" | cut -f1)
    echo -e "${GREEN}✓ 数据库备份完成: $BACKUP_FILE ($BACKUP_SIZE)${NC}"
else
    echo -e "${RED}✗ 数据库备份失败${NC}"
    exit 1
fi

unset PGPASSWORD

# 创建元数据文件
cat > "${BACKUP_FILE}.meta.json" <<EOF
{
  "type": "database",
  "filename": "$(basename $BACKUP_FILE)",
  "size": $(stat -c%s "$BACKUP_FILE" 2>/dev/null || stat -f%z "$BACKUP_FILE" 2>/dev/null),
  "created_at": "$(date -Iseconds)",
  "database": "$DB_NAME",
  "status": "completed"
}
EOF

echo ""

# ==================== 文件备份 ====================
echo -e "${YELLOW}[2/3] 备份文件...${NC}"

FILES_BACKUP="$FILES_BACKUP_DIR/files_backup_${TIMESTAMP}.tar.gz"

# 需要备份的目录
DIRECTORIES_TO_BACKUP=()

if [ -d "/app/media" ]; then
    DIRECTORIES_TO_BACKUP+=("/app/media")
fi

if [ -d "/app/upload_chunks" ]; then
    DIRECTORIES_TO_BACKUP+=("/app/upload_chunks")
fi

if [ -d "/app/static" ]; then
    DIRECTORIES_TO_BACKUP+=("/app/static")
fi

if [ -d "/app/themes" ]; then
    DIRECTORIES_TO_BACKUP+=("/app/themes")
fi

if [ -d "/app/plugins" ]; then
    DIRECTORIES_TO_BACKUP+=("/app/plugins")
fi

if [ ${#DIRECTORIES_TO_BACKUP[@]} -gt 0 ]; then
    if tar -czf "$FILES_BACKUP" "${DIRECTORIES_TO_BACKUP[@]}" 2>/dev/null; then
        BACKUP_SIZE=$(du -h "$FILES_BACKUP" | cut -f1)
        echo -e "${GREEN}✓ 文件备份完成: $FILES_BACKUP ($BACKUP_SIZE)${NC}"
        
        # 创建元数据文件
        cat > "${FILES_BACKUP}.meta.json" <<EOF
{
  "type": "files",
  "filename": "$(basename $FILES_BACKUP)",
  "size": $(stat -c%s "$FILES_BACKUP" 2>/dev/null || stat -f%z "$FILES_BACKUP" 2>/dev/null),
  "created_at": "$(date -Iseconds)",
  "directories": $(printf '%s\n' "${DIRECTORIES_TO_BACKUP[@]}" | jq -R . | jq -s .),
  "status": "completed"
}
EOF
    else
        echo -e "${YELLOW}⚠ 文件备份跳过（无文件或失败）${NC}"
    fi
else
    echo -e "${YELLOW}⚠ 文件备份跳过（无目录）${NC}"
fi

echo ""

# ==================== 清理旧备份 ====================
echo -e "${YELLOW}[3/3] 清理旧备份（保留${RETENTION_DAYS}天）...${NC}"

# 删除过期的数据库备份
DELETED_DB_COUNT=0
while IFS= read -r -d '' file; do
    rm -f "$file"
    DELETED_DB_COUNT=$((DELETED_DB_COUNT + 1))
done < <(find "$DATABASE_BACKUP_DIR" -name "*.sql.gz" -mtime +$RETENTION_DAYS -print0)

# 删除过期的文件备份
DELETED_FILES_COUNT=0
while IFS= read -r -d '' file; do
    rm -f "$file"
    DELETED_FILES_COUNT=$((DELETED_FILES_COUNT + 1))
done < <(find "$FILES_BACKUP_DIR" -name "*.tar.gz" -mtime +$RETENTION_DAYS -print0)

# 删除孤立的元数据文件
find "$DATABASE_BACKUP_DIR" -name "*.meta.json" ! -name "*.sql.gz.meta.json" -delete 2>/dev/null || true
find "$FILES_BACKUP_DIR" -name "*.meta.json" ! -name "*.tar.gz.meta.json" -delete 2>/dev/null || true

echo -e "${GREEN}✓ 清理完成: 删除 $DELETED_DB_COUNT 个数据库备份, $DELETED_FILES_COUNT 个文件备份${NC}"

echo ""

# ==================== 备份统计 ====================
echo "========================================="
echo -e "${GREEN}  备份完成!${NC}"
echo "========================================="
echo ""

# 统计备份数量和大小
DB_BACKUP_COUNT=$(find "$DATABASE_BACKUP_DIR" -name "*.sql.gz" | wc -l)
FILES_BACKUP_COUNT=$(find "$FILES_BACKUP_DIR" -name "*.tar.gz" | wc -l)
DB_TOTAL_SIZE=$(du -sh "$DATABASE_BACKUP_DIR" | cut -f1)
FILES_TOTAL_SIZE=$(du -sh "$FILES_BACKUP_DIR" | cut -f1)

echo "数据库备份: $DB_BACKUP_COUNT 个 (总大小: $DB_TOTAL_SIZE)"
echo "文件备份: $FILES_BACKUP_COUNT 个 (总大小: $FILES_TOTAL_SIZE)"
echo "保留策略: $RETENTION_DAYS 天"
echo ""
echo "备份位置: $BACKUP_DIR"
echo ""
