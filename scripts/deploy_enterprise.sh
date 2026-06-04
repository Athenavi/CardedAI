#!/bin/bash
# FastBlog 企业版一键部署脚本
# 支持 Ubuntu/CentOS/Debian

set -e

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# 日志函数
log_info() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

log_warn() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# 检测操作系统
detect_os() {
    if [ -f /etc/os-release ]; then
        . /etc/os-release
        OS=$ID
        VERSION=$VERSION_ID
    else
        log_error "无法检测操作系统"
        exit 1
    fi
    log_info "检测到操作系统: $OS $VERSION"
}

# 检查root权限
check_root() {
    if [ "$EUID" -ne 0 ]; then
        log_error "请使用 root 权限运行此脚本"
        exit 1
    fi
}

# 安装系统依赖
install_dependencies() {
    log_info "安装系统依赖..."
    
    case $OS in
        ubuntu|debian)
            apt-get update
            apt-get install -y \
                python3 \
                python3-pip \
                python3-venv \
                nginx \
                postgresql \
                postgresql-contrib \
                redis-server \
                supervisor \
                git \
                curl \
                wget \
                certbot \
                python3-certbot-nginx
            ;;
        centos|rhel|fedora)
            yum install -y \
                python3 \
                python3-pip \
                nginx \
                postgresql-server \
                postgresql-contrib \
                redis \
                supervisor \
                git \
                curl \
                wget \
                epel-release
            yum install -y certbot python3-certbot-nginx
            ;;
        *)
            log_error "不支持的操作系统: $OS"
            exit 1
            ;;
    esac
    
    log_info "系统依赖安装完成"
}

# 配置 PostgreSQL
setup_postgresql() {
    log_info "配置 PostgreSQL..."
    
    case $OS in
        ubuntu|debian)
            systemctl enable postgresql
            systemctl start postgresql
            ;;
        centos|rhel|fedora)
            postgresql-setup --initdb
            systemctl enable postgresql
            systemctl start postgresql
            ;;
    esac
    
    # 创建数据库和用户
    sudo -u postgres psql <<EOF
CREATE USER fastblog WITH PASSWORD 'fastblog_password';
CREATE DATABASE fastblog OWNER fastblog;
GRANT ALL PRIVILEGES ON DATABASE fastblog TO fastblog;
EOF
    
    log_info "PostgreSQL 配置完成"
}

# 配置 Redis
setup_redis() {
    log_info "配置 Redis..."
    
    systemctl enable redis
    systemctl start redis
    
    log_info "Redis 配置完成"
}

# 安装 FastBlog
install_fastblog() {
    log_info "安装 FastBlog..."
    
    # 创建应用目录
    mkdir -p /opt/fastblog
    cd /opt/fastblog
    
    # 克隆或复制代码
    if [ -d ".git" ]; then
        git pull
    else
        log_warn "请手动将 FastBlog 代码复制到 /opt/fastblog"
        return
    fi
    
    # 创建虚拟环境
    python3 -m venv venv
    source venv/bin/activate
    
    # 安装依赖
    pip install --upgrade pip
    pip install -r requirements.txt
    
    # 创建必要目录
    mkdir -p storage logs backups
    
    # 设置权限
    chown -R www-data:www-data /opt/fastblog
    
    log_info "FastBlog 安装完成"
}

# 配置 Nginx
setup_nginx() {
    log_info "配置 Nginx..."
    
    cat > /etc/nginx/sites-available/fastblog <<'EOF'
server {
    listen 80;
    server_name _;
    
    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
    
    location /static {
        alias /opt/fastblog/static;
        expires 30d;
    }
    
    location /media {
        alias /opt/fastblog/media;
        expires 30d;
    }
}
EOF
    
    ln -sf /etc/nginx/sites-available/fastblog /etc/nginx/sites-enabled/
    nginx -t
    systemctl restart nginx
    
    log_info "Nginx 配置完成"
}

# 配置 Supervisor
setup_supervisor() {
    log_info "配置 Supervisor..."
    
    cat > /etc/supervisor/conf.d/fastblog.conf <<'EOF'
[program:fastblog]
command=/opt/fastblog/venv/bin/python main.py
directory=/opt/fastblog
user=www-data
autostart=true
autorestart=true
stopasgroup=true
killasgroup=true
stdout_logfile=/opt/fastblog/logs/supervisor.log
stderr_logfile=/opt/fastblog/logs/supervisor_error.log
environment=PYTHONPATH="/opt/fastblog"
EOF
    
    supervisorctl reread
    supervisorctl update
    supervisorctl start fastblog
    
    log_info "Supervisor 配置完成"
}

# 配置 SSL 证书
setup_ssl() {
    log_info "配置 SSL 证书..."
    
    read -p "请输入域名: " DOMAIN
    
    certbot --nginx -d $DOMAIN --non-interactive --agree-tos --email admin@$DOMAIN
    
    log_info "SSL 证书配置完成"
}

# 配置防火墙
setup_firewall() {
    log_info "配置防火墙..."
    
    case $OS in
        ubuntu|debian)
            ufw allow ssh
            ufw allow http
            ufw allow https
            ufw --force enable
            ;;
        centos|rhel|fedora)
            firewall-cmd --permanent --add-service=ssh
            firewall-cmd --permanent --add-service=http
            firewall-cmd --permanent --add-service=https
            firewall-cmd --reload
            ;;
    esac
    
    log_info "防火墙配置完成"
}

# 创建备份脚本
create_backup_script() {
    log_info "创建备份脚本..."
    
    cat > /opt/fastblog/backup.sh <<'EOF'
#!/bin/bash
BACKUP_DIR="/opt/fastblog/backups"
DATE=$(date +%Y%m%d_%H%M%S)

# 备份数据库
pg_dump -U fastblog fastblog | gzip > $BACKUP_DIR/db_backup_$DATE.sql.gz

# 备份文件
tar -czf $BACKUP_DIR/files_backup_$DATE.tar.gz /opt/fastblog/media /opt/fastblog/static

# 保留最近7天的备份
find $BACKUP_DIR -name "*.gz" -mtime +7 -delete

echo "Backup completed: $DATE"
EOF
    
    chmod +x /opt/fastblog/backup.sh
    
    # 添加定时任务
    (crontab -l 2>/dev/null; echo "0 2 * * * /opt/fastblog/backup.sh") | crontab -
    
    log_info "备份脚本创建完成"
}

# 主函数
main() {
    log_info "开始 FastBlog 企业版部署..."
    
    check_root
    detect_os
    install_dependencies
    setup_postgresql
    setup_redis
    install_fastblog
    setup_nginx
    setup_supervisor
    create_backup_script
    
    log_info "是否配置 SSL 证书？(y/n)"
    read -p "> " SETUP_SSL
    if [ "$SETUP_SSL" = "y" ]; then
        setup_ssl
    fi
    
    setup_firewall
    
    log_info "=========================================="
    log_info "FastBlog 企业版部署完成！"
    log_info "=========================================="
    log_info "访问地址: http://your-domain"
    log_info "数据库: PostgreSQL (fastblog/fastblog_password)"
    log_info "缓存: Redis"
    log_info "进程管理: Supervisor"
    log_info "Web服务器: Nginx"
    log_info "=========================================="
    log_warn "请修改默认数据库密码！"
    log_warn "请配置环境变量文件 (.env)！"
}

# 执行主函数
main
