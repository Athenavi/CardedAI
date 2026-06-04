#!/bin/bash
# FastBlog 一键安装脚本 (Linux)
# 支持 Ubuntu, Debian, CentOS, Fedora

set -e

echo "========================================="
echo "  FastBlog 一键安装脚本"
echo "========================================="
echo ""

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# 检测操作系统
detect_os() {
    if [ -f /etc/os-release ]; then
        . /etc/os-release
        OS=$ID
        VERSION=$VERSION_ID
    else
        echo -e "${RED}无法检测操作系统${NC}"
        exit 1
    fi
    echo -e "${GREEN}检测到操作系统: $OS $VERSION${NC}"
}

# 检查Docker
check_docker() {
    if ! command -v docker &> /dev/null; then
        echo -e "${YELLOW}Docker未安装，正在安装...${NC}"
        install_docker
    else
        echo -e "${GREEN}Docker已安装: $(docker --version)${NC}"
    fi
}

# 检查Docker Compose
check_docker_compose() {
    if ! command -v docker-compose &> /dev/null && ! docker compose version &> /dev/null; then
        echo -e "${YELLOW}Docker Compose未安装，正在安装...${NC}"
        install_docker_compose
    else
        echo -e "${GREEN}Docker Compose已安装${NC}"
    fi
}

# 安装Docker
install_docker() {
    case $OS in
        ubuntu|debian)
            apt-get update
            apt-get install -y apt-transport-https ca-certificates curl software-properties-common
            curl -fsSL https://download.docker.com/linux/$OS/gpg | apt-key add -
            add-apt-repository "deb [arch=amd64] https://download.docker.com/linux/$OS $VERSION stable"
            apt-get update
            apt-get install -y docker-ce docker-ce-cli containerd.io
            ;;
        centos|fedora)
            yum install -y yum-utils
            yum-config-manager --add-repo https://download.docker.com/linux/centos/docker-ce.repo
            yum install -y docker-ce docker-ce-cli containerd.io
            systemctl enable docker
            systemctl start docker
            ;;
        *)
            echo -e "${RED}不支持的操作系统: $OS${NC}"
            exit 1
            ;;
    esac
    echo -e "${GREEN}Docker安装完成${NC}"
}

# 安装Docker Compose
install_docker_compose() {
    curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
    chmod +x /usr/local/bin/docker-compose
    echo -e "${GREEN}Docker Compose安装完成${NC}"
}

# 创建.env文件
create_env_file() {
    if [ ! -f .env ]; then
        echo -e "${YELLOW}创建.env配置文件...${NC}"
        cp .env_example .env
        
        # 生成随机密钥
        SECRET_KEY=$(openssl rand -base64 32)
        sed -i "s/SECRET_KEY=.*/SECRET_KEY=$SECRET_KEY/" .env
        
        echo -e "${GREEN}.env文件创建完成${NC}"
    else
        echo -e "${GREEN}.env文件已存在${NC}"
    fi
}

# 创建必要目录
create_directories() {
    echo -e "${YELLOW}创建必要目录...${NC}"
    mkdir -p media upload_chunks static themes plugins translations backups logs storage
    mkdir -p nginx/conf.d ssl
    echo -e "${GREEN}目录创建完成${NC}"
}

# 启动服务
start_services() {
    echo -e "${YELLOW}启动FastBlog服务...${NC}"
    
    # 使用docker compose或docker-compose
    if docker compose version &> /dev/null; then
        docker compose up -d
    else
        docker-compose up -d
    fi
    
    echo -e "${GREEN}服务启动完成${NC}"
}

# 等待服务就绪
wait_for_services() {
    echo -e "${YELLOW}等待服务就绪...${NC}"
    sleep 10
    
    # 检查应用健康状态
    for i in {1..30}; do
        if curl -f http://localhost:9421/api/v1/health &> /dev/null; then
            echo -e "${GREEN}FastBlog已就绪!${NC}"
            return 0
        fi
        echo -n "."
        sleep 2
    done
    
    echo -e "${RED}服务启动超时${NC}"
    return 1
}

# 显示安装信息
show_info() {
    echo ""
    echo "========================================="
    echo -e "${GREEN}  FastBlog 安装完成!${NC}"
    echo "========================================="
    echo ""
    echo "访问地址: http://localhost:9421"
    echo ""
    echo "常用命令:"
    echo "  查看日志: docker-compose logs -f app"
    echo "  停止服务: docker-compose down"
    echo "  重启服务: docker-compose restart"
    echo "  备份数据: docker-compose exec app python scripts/cli.py backup"
    echo ""
    echo "配置文件: .env"
    echo "数据目录: ./media, ./storage, ./backups"
    echo ""
}

# 主函数
main() {
    detect_os
    check_docker
    check_docker_compose
    create_env_file
    create_directories
    start_services
    wait_for_services
    show_info
}

# 执行主函数
main
