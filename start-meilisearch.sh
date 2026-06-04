#!/bin/bash

# Meilisearch 快速启动脚本
# 用于快速部署和配置 Meilisearch 搜索引擎

set -e

echo "=========================================="
echo "  FastBlog Meilisearch 快速启动"
echo "=========================================="
echo ""

# 检查 Docker 是否安装
if ! command -v docker &> /dev/null; then
    echo "❌ Docker 未安装，请先安装 Docker"
    exit 1
fi

# 检查 Docker Compose 是否安装
if ! command -v docker-compose &> /dev/null && ! docker compose version &> /dev/null; then
    echo "❌ Docker Compose 未安装，请先安装 Docker Compose"
    exit 1
fi

# 确定使用的 docker-compose 命令
if docker compose version &> /dev/null; then
    DOCKER_COMPOSE="docker compose"
else
    DOCKER_COMPOSE="docker-compose"
fi

echo "✅ Docker 和 Docker Compose 已安装"
echo ""

# 创建数据目录
echo "📁 创建数据目录..."
mkdir -p meili_data
echo "✅ 数据目录已创建"
echo ""

# 启动 Meilisearch
echo "🚀 启动 Meilisearch..."
$DOCKER_COMPOSE -f docker-compose.meilisearch.yml up -d

echo ""
echo "⏳ 等待 Meilisearch 启动..."
sleep 5

# 检查服务状态
if $DOCKER_COMPOSE -f docker-compose.meilisearch.yml ps | grep -q "Up"; then
    echo "✅ Meilisearch 已成功启动！"
    echo ""
    echo "📊 服务信息:"
    echo "   - 地址: http://localhost:7700"
    echo "   - 健康检查: http://localhost:7700/health"
    echo ""
    echo "🔧 下一步操作:"
    echo "   1. 在 FastBlog 后台激活'全文搜索引擎'插件"
    echo "   2. 配置插件设置（服务器地址: http://localhost:7700）"
    echo "   3. 执行索引重建以导入现有文章"
    echo ""
    echo "📝 常用命令:"
    echo "   - 查看日志: $DOCKER_COMPOSE -f docker-compose.meilisearch.yml logs -f"
    echo "   - 停止服务: $DOCKER_COMPOSE -f docker-compose.meilisearch.yml down"
    echo "   - 重启服务: $DOCKER_COMPOSE -f docker-compose.meilisearch.yml restart"
    echo ""
else
    echo "❌ Meilisearch 启动失败，请检查日志:"
    $DOCKER_COMPOSE -f docker-compose.meilisearch.yml logs
    exit 1
fi
