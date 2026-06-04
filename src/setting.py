import os
from datetime import timedelta
from pathlib import Path

from dotenv import load_dotenv

# 加载 .env 文件
# 优先加载根目录 .env（本地开发模式），再加载 config/.env 作为补充
# 在 Docker 模式下，环境变量由 docker-compose.yml 的 environment 注入，不会被覆盖
load_dotenv()  # 根目录 .env 优先（本地开发模式，DB_HOST=localhost 等）
load_dotenv(Path(__file__).parent.parent / "config" / ".env")  # config/.env 作为补充，已加载的值不会被覆盖

# 全局标志：跟踪数据库 URI 是否已经打印过（当前进程内）
_db_uri_printed = False


def _get_worker_info():
    """获取当前 worker 进程信息"""
    import multiprocessing
    try:
        current_process = multiprocessing.current_process()
        # 如果是主进程
        if current_process.name == 'MainProcess':
            return "[Worker-Main]"
        # 如果是子进程，提取进程 ID
        identity = getattr(current_process, '_identity', None)
        if identity and len(identity) > 0:
            return f"[Worker-{identity[0]}]"
        return f"[Worker-{current_process.pid}]"
    except Exception:
        return "[Worker-?]"


def get_sqlalchemy_uri(db_config):
    """获取SQLAlchemy数据库URI，仅支持PostgreSQL"""
    db_engine = db_config.get('db_engine', 'postgresql').lower()
    db_host = db_config.get('db_host')
    db_user = db_config.get('db_user')
    db_port = db_config.get('db_port')
    db_name = db_config.get('db_name')
    db_password = db_config.get('db_password')

    # 检查必要配置
    if not all([db_host, db_user, db_port, db_name]):
        print(
            'The database connection configuration is incomplete. Please check the .env file or environment variables.')
        print('This is normal during installation wizard - configuration will be set up through the installer.')
        return None

    # 对于IPv6地址，需要使用方括号包围主机地址
    if ':' in db_host and not db_host.startswith('[') and not db_host.endswith(']'):  # 检查是否为IPv6地址
        formatted_host = f"[{db_host}]"
    else:
        formatted_host = db_host
    password_part = f":{db_password}" if db_password else ""
    sqlalchemy_uri = f"postgresql+psycopg2://{db_user}{password_part}@{formatted_host}:{db_port}/{db_name}"

    # 安全日志，如果密码存在则隐藏
    if db_password:
        safe_uri = sqlalchemy_uri.replace(db_password, '***')
    else:
        safe_uri = sqlalchemy_uri

    # 使用环境变量标记当前进程是否已输出数据库信息
    import os
    worker_info = _get_worker_info()
    env_key = f"DB_INFO_PRINTED_{os.getpid()}"

    if not os.environ.get(env_key):
        print(f"{worker_info} 数据库引擎：PostgreSQL")
        print(f"{worker_info} SQLAlchemy URI: {safe_uri}")
        os.environ[env_key] = "1"  # 标记为已打印

    return sqlalchemy_uri


class BaseConfig:
    """基础配置类"""
    global_encoding = 'utf-8'
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    SECRET_KEY = os.environ.get('SECRET_KEY') or os.urandom(32).hex()

    # 使用条件判断处理可能的 None 值
    jwt_expiration = os.getenv('JWT_EXPIRATION_DELTA')
    JWT_EXPIRATION_DELTA = int(jwt_expiration) if jwt_expiration is not None else 7200

    refresh_expiration = os.getenv('REFRESH_TOKEN_EXPIRATION_DELTA')
    REFRESH_TOKEN_EXPIRATION_DELTA = int(refresh_expiration) if refresh_expiration is not None else 64800

    TIME_ZONE = os.getenv('TIME_ZONE') or 'Asia/Shanghai'

    domain_env = os.getenv('DOMAIN')
    domain = (domain_env.rstrip('/') + '/') if domain_env is not None else '/'

    sitename = os.getenv('TITLE') or 'zyblog'
    beian = os.getenv('BEIAN') or '京ICP备12345678号'

    # 数据库引擎配置（仅支持 PostgreSQL）
    DB_ENGINE = 'postgresql'

    # 注意：这里暂时设为None，在子类中具体设置
    SQLALCHEMY_DATABASE_URI = None
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # 添加数据库回显选项，用于调试
    database_echo = os.getenv('DATABASE_ECHO', 'False').lower() == 'true'

    CACHE_TYPE = 'simple'
    SESSION_COOKIE_NAME = 'zb_session'
    PERMANENT_SESSION_LIFETIME = timedelta(hours=48)
    TEMP_FOLDER = 'temp/upload'
    AVATAR_SERVER = "https://api.7trees.cn/avatar"
    ALLOWED_MIMES = [
        # 常见图片格式
        'image/jpeg',
        'image/png',
        'image/gif',
        'image/bmp',
        'image/tiff',
        'image/webp',
        'image/svg+xml',
        # 常见视频格式
        'video/mp4',
        'video/avi',
        'video/mpeg',
        'video/quicktime',
        'video/x-msvideo',
        'video/mp2t',
        'video/x-flv',
        'video/webm',
        'video/x-m4v',
        'video/3gpp',
        'video/x-matroska',  # .mkv
        # 常见音频格式
        'audio/wav',
        'audio/mpeg',
        'audio/ogg',
        'audio/flac',
        'audio/aac',
        'audio/mp3',
        'audio/x-wav',
        'audio/mp4',  # .m4a
        # 文档格式
        'application/pdf',
        'application/msword',  # .doc
        'application/vnd.openxmlformats-officedocument.wordprocessingml.document',  # .docx
        'application/vnd.ms-excel',  # .xls
        'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',  # .xlsx
        'application/vnd.ms-powerpoint',  # .ppt
        'application/vnd.openxmlformats-officedocument.presentationml.presentation',  # .pptx
        'text/plain',  # .txt
        'text/markdown',  # .md
        'text/csv',  # .csv
        'text/html',  # .html
        # 压缩格式
        'application/zip',
        'application/x-zip-compressed',  # ZIP 文件的另一种 MIME 类型
        'application/x-rar-compressed',
        'application/x-7z-compressed',
        'application/gzip',
        'application/x-tar',
        'application/x-bzip2',
        # 其他常见格式
        'application/json',
        'application/xml',
        'application/octet-stream',  # 通用二进制文件
    ]
    UPLOAD_LIMIT = 60 * 1024 * 1024
    MAX_LINE = 1000
    MAX_CACHE_TIMESTAMP = 7200
    USER_FREE_STORAGE_LIMIT = 0.5 * 1024 * 1024 * 1024  # 512MB 用户免费空间限制
    RATELIMIT_DEFAULT = "10/second"

    # FFmpeg 配置（视频处理）
    FFMPEG_PATH = os.environ.get('FFMPEG_PATH', 'ffmpeg')
    FFPROBE_PATH = os.environ.get('FFPROBE_PATH', 'ffprobe')
    # 邮件配置
    MAIL_SERVER = os.environ.get('MAIL_SERVER', 'smtp.gmail.com')  # 默认使用 Gmail SMTP
    MAIL_PORT = int(os.environ.get('MAIL_PORT', 587))
    MAIL_USE_TLS = os.environ.get('MAIL_USE_TLS', 'True').lower() == 'true'
    MAIL_USERNAME = os.environ.get('MAIL_USERNAME')
    MAIL_PASSWORD = os.environ.get('MAIL_PASSWORD')
    BABEL_DEFAULT_LOCALE = 'zh_CN'
    BABEL_DEFAULT_TIMEZONE = 'Asia/Shanghai'
    BABEL_SUPPORTED_LOCALES = ['zh_CN', "en"]
    BABEL_TRANSLATION_DIRECTORIES = 'translations'
    # jwt
    JWT_SECRET_KEY = os.environ.get('JWT_SECRET_KEY') or SECRET_KEY
    JWT_ALGORITHM = "HS256"  # JWT 算法
    JWT_ACCESS_TOKEN_EXPIRES = timedelta(seconds=JWT_EXPIRATION_DELTA)
    JWT_REFRESH_TOKEN_EXPIRES = timedelta(seconds=REFRESH_TOKEN_EXPIRATION_DELTA)
    JWT_ACCESS_COOKIE_NAME = 'access_token'
    JWT_REFRESH_COOKIE_NAME = 'refresh_token'
    JWT_TOKEN_LOCATION = ['cookies']
    JWT_COOKIE_SECURE = False
    JWT_COOKIE_CSRF_PROTECT = False
    JWT_COOKIE_SAMESITE = 'Lax'  # 添加SameSite属性以防范CSRF攻击
    JWT_SESSION_COOKIE = False
    REMEMBER_COOKIE_DURATION = timedelta(days=30)  # 记住登录状态30天
    PERMANENT_SESSION_LIFETIME = timedelta(days=30)
    # S3存储配置
    S3_ENABLED = os.environ.get('S3_ENABLED', 'True').lower() == 'true'
    S3_ENDPOINT_URL = os.environ.get('S3_ENDPOINT_URL')  # S3服务端点，如使用AWS S3可不设置
    S3_ACCESS_KEY = os.environ.get('S3_ACCESS_KEY')  # S3访问密钥
    S3_SECRET_KEY = os.environ.get('S3_SECRET_KEY')  # S3密钥
    S3_BUCKET_NAME = os.environ.get('S3_BUCKET_NAME', 'media-bucket')  # S3存储桶名称
    S3_REGION = os.environ.get('S3_REGION', 'us-east-1')  # S3区域
    S3_USE_SSL = os.environ.get('S3_USE_SSL', 'True').lower() == 'true'  # 是否使用SSL
    S3_SIGNATURE_VERSION = os.environ.get('S3_SIGNATURE_VERSION', 's3v4')  # 签名版本

    # 安全头配置（Talisman）
    TALISMAN_CONTENT_SECURITY_POLICY = {
        'default-src': "'self'",
        'script-src': ["'self'", "cdn.example.com"],
        'style-src': ["'self'", "'unsafe-inline'"]
    }


class AppConfig(BaseConfig):
    """应用配置类，可以继承基础配置并进行覆盖或添加"""

    def __init__(self):
        super().__init__()
        # 初始化数据库URI（可能为 None，如果配置不完整）
        self.database_url = self._get_database_uri()
        # 为SQLAlchemy设置数据库URI
        self.SQLALCHEMY_DATABASE_URI = self.database_url

    db_engine = os.environ.get('DB_ENGINE') or os.getenv('DB_ENGINE', 'postgresql')
    db_host = os.environ.get('DB_HOST') or os.getenv('DATABASE_HOST', 'localhost')
    db_user = os.environ.get('DB_USER') or os.getenv('DATABASE_USER', 'postgres')
    db_name = os.environ.get('DB_NAME') or os.getenv('DATABASE_NAME')
    db_password = os.environ.get('DB_PASSWORD') or os.getenv('DATABASE_PASSWORD')
    db_port_env = os.environ.get('DB_PORT') or os.getenv('DATABASE_PORT')
    db_port = int(db_port_env) if db_port_env is not None else 5432
    db_pool_size_env = os.environ.get('DB_POOL_SIZE') or os.getenv('DATABASE_POOL_SIZE')
    db_pool_size = int(db_pool_size_env) if db_pool_size_env is not None else 50
    db_pool_overflow_env = os.environ.get('DB_POOL_OVERFLOW') or os.getenv('DATABASE_POOL_OVERFLOW')
    db_pool_overflow = int(db_pool_overflow_env) if db_pool_overflow_env is not None else 100
    db_pool_timeout_env = os.environ.get('DB_POOL_TIMEOUT') or os.getenv('DATABASE_POOL_TIMEOUT')
    db_pool_timeout = int(db_pool_timeout_env) if db_pool_timeout_env is not None else 60
    db_table_prefix = os.environ.get('DB_TABLE_PREFIX') or os.getenv('DB_TABLE_PREFIX', '')

    def _get_database_uri(self):
        """获取数据库URI"""
        return get_sqlalchemy_uri({
            'db_engine': self.db_engine,
            'db_host': self.db_host,
            'db_user': self.db_user,
            'db_port': self.db_port,
            'db_name': self.db_name,
            'db_password': self.db_password
        })

    @property
    def database_pool_size(self):
        """动态获取连接池大小"""
        return self.db_pool_size

    @property
    def database_pool_overflow(self):
        """动态获取连接池溢出数"""
        return self.db_pool_overflow

    @property
    def database_pool_timeout(self):
        """动态获取连接池超时"""
        return self.db_pool_timeout

    @property
    def pool_config(self):
        """动态获取连接池配置（PostgreSQL）"""
        return {
            "pool_size": int(self.db_pool_size),
            "max_overflow": int(self.db_pool_overflow),
            "pool_timeout": int(self.db_pool_timeout),
            "pool_recycle": 1200,
            "pool_pre_ping": True,
        }

    # RedisConfig = {
    #    "host": os.environ.get('REDIS_HOST') or os.getenv('REDIS_HOST', 'localhost'),
    #    "port": os.environ.get('REDIS_PORT') or os.getenv('REDIS_PORT', 6379),
    #    "db": os.environ.get('REDIS_DB') or os.getenv('REDIS_DB', 0),
    #    "password": os.environ.get('REDIS_PASSWORD') or os.getenv('REDIS_PASSWORD') or None,
    #    "decode_responses": True,
    #    "socket_connect_timeout": 3,  # 连接超时3秒
    #    "socket_timeout": 3,  # 读写超时3秒
    #    "retry_on_timeout": True,  # 超时重试
    #    "max_connections": 10  # 连接池大小
    # }


#

class WechatPayConfig:
    # 微信支付配置 (服务商模式或直连模式)
    WECHAT_APPID = os.getenv('WECHAT_APPID')  # 小程序/公众号AppID
    WECHAT_MCHID = os.getenv('WECHAT_MCHID')  # 商户号
    WECHAT_API_V3_KEY = os.getenv('WECHAT_API_V3_KEY')  # APIv3密钥

    # 私钥可以是文件路径或者直接的内容
    private_key_env = os.getenv('WECHAT_PRIVATE_KEY')
    if private_key_env:
        # 如果环境变量中提供了私钥内容或者是文件路径
        WECHAT_PRIVATE_KEY = private_key_env
    else:
        # 默认从文件读取
        private_key_path = Path('keys/wechat/private_key.pem')
        WECHAT_PRIVATE_KEY = None
        if private_key_path.exists():
            try:
                WECHAT_PRIVATE_KEY = private_key_path.read_text(encoding='utf-8')
            except UnicodeDecodeError:
                # 尝试使用其他编码读取文件
                try:
                    WECHAT_PRIVATE_KEY = private_key_path.read_text(encoding='gbk')
                except UnicodeDecodeError:
                    # 如果仍然失败，以二进制方式读取
                    WECHAT_PRIVATE_KEY = private_key_path.read_bytes().decode('utf-8', errors='ignore')

    WECHAT_CERT_SERIAL_NO = os.getenv('WECHAT_CERT_SERIAL_NO')  # 证书序列号
    WECHAT_NOTIFY_URL = os.getenv('WECHAT_NOTIFY_URL', 'https://yourdomain.com/api/payment/wechat/notify')
    WECHAT_CERT_DIR = os.getenv('WECHAT_CERT_DIR', './cert')


class AliPayConfig:
    # 支付宝配置

    def __init__(self):
        # 延迟导入以避免循环导入
        try:
            # 延迟导入以避免循环导入
            def get_site_domain():
                # 简化版本的域名获取逻辑
                return os.getenv('DOMAIN', 'http://localhost:9421/')

            # 获取domain，优先使用get_site_domain()函数获取的值
            domain = get_site_domain() or os.getenv('DOMAIN')
            domain = (domain.rstrip('/') + '/') if domain is not None else '/'
        except Exception:
            # 如果获取失败，则使用环境变量或默认值
            domain = os.getenv('DOMAIN', 'http://localhost:9421/')
            domain = (domain.rstrip('/') + '/') if domain is not None else '/'

        if domain is None:
            print("域名配置有问题")

        self.ALIPAY_APPID = os.getenv('ALIPAY_APPID')
        self.ALIPAY_DEBUG = os.getenv('ALIPAY_DEBUG', 'True').lower() == 'true'  # 沙箱模式设为True
        self.ALIPAY_GATEWAY = 'https://openapi.alipaydev.com/gateway.do' if self.ALIPAY_DEBUG else 'https://openapi.alipay.com/gateway.do'
        self.ALIPAY_RETURN_URL = os.getenv('ALIPAY_RETURN_URL', f'{domain}api/payment/alipay/return')  # 同步回调(网页支付)
        self.ALIPAY_NOTIFY_URL = os.getenv('ALIPAY_NOTIFY_URL', f'{domain}api/payment/alipay/notify')  # 异步回调
        # 密钥字符串 (推荐从环境变量或文件读取)
        private_key_path = Path('keys/alipay/app_private_key.pem')
        if private_key_path.exists():
            try:
                self.ALIPAY_PRIVATE_KEY_STRING = private_key_path.read_text(encoding='utf-8')
            except UnicodeDecodeError:
                # 尝试使用其他编码读取文件
                try:
                    self.ALIPAY_PRIVATE_KEY_STRING = private_key_path.read_text(encoding='gbk')
                except UnicodeDecodeError:
                    # 如果仍然失败，以二进制方式读取
                    self.ALIPAY_PRIVATE_KEY_STRING = private_key_path.read_bytes().decode('utf-8', errors='ignore')
            except Exception as e:
                # 其他错误也应妥善处理
                print(f"读取支付宝私钥文件失败: {str(e)}")
                self.ALIPAY_PRIVATE_KEY_STRING = None
        else:
            self.ALIPAY_PRIVATE_KEY_STRING = None

        public_key_path = Path('keys/alipay/alipay_public_key.pem')
        if public_key_path.exists():
            try:
                self.ALIPAY_PUBLIC_KEY_STRING = public_key_path.read_text(encoding='utf-8')
            except UnicodeDecodeError:
                # 尝试使用其他编码读取文件
                try:
                    self.ALIPAY_PUBLIC_KEY_STRING = public_key_path.read_text(encoding='gbk')
                except UnicodeDecodeError:
                    # 如果仍然失败，以二进制方式读取
                    self.ALIPAY_PUBLIC_KEY_STRING = public_key_path.read_bytes().decode('utf-8', errors='ignore')
            except Exception as e:
                # 其他错误也应妥善处理
                print(f"读取支付宝公钥文件失败: {str(e)}")
                self.ALIPAY_PUBLIC_KEY_STRING = None
        else:
            self.ALIPAY_PUBLIC_KEY_STRING = None


# 延迟导入以避免循环导入
def get_app_config():
    # 使用密码学安全的 secrets 模块生成密钥
    import secrets
    # 更新 BaseConfig 中的 SECRET_KEY
    secret_key = os.environ.get('SECRET_KEY')
    if not secret_key:
        # 未配置环境变量时，生成强随机密钥并警告用户
        secret_key = secrets.token_urlsafe(32)
        print("=" * 60)
        print("警告：未设置 SECRET_KEY 环境变量，已生成临时随机密钥。")
        print(f"临时密钥：{secret_key}")
        print("请在生产环境中设置 SECRET_KEY 环境变量以确保 Token 稳定性。")
        print("=" * 60)

    BaseConfig.SECRET_KEY = secret_key

    # 获取domain环境变量
    domain_env = os.getenv('DOMAIN')
    BaseConfig.domain = (domain_env.rstrip('/') + '/') if domain_env is not None else '/'

    # 创建AppConfig实例并初始化数据库URI
    config = AppConfig()
    return config


app_config = get_app_config()
settings = app_config  # 为FastAPI兼容性创建别名


class ProductionConfig(AppConfig):
    """生产环境配置"""

    def __init__(self):
        super().__init__()
        self.DEBUG = False
        self.TESTING = False
        self._validate_required_env()

    def _validate_required_env(self):
        """校验生产环境必需的数据库配置，使用 AppConfig 已解析的属性（带默认值）。
        仅发出警告而不终止进程——应用设计为在数据库未配置时仍能启动（安装向导）。
        """
        missing = []
        # 使用 AppConfig 解析后的属性（有 fallback 默认值），而非原始 os.environ.get()
        if not self.db_name:
            missing.append('DB_NAME')
        if not self.db_host:
            missing.append('DB_HOST')
        if not self.db_user:
            missing.append('DB_USER')

        if missing:
            print("=" * 70)
            print("⚠️  警告：以下数据库环境变量未设置，应用将以安装向导模式启动")
            print("=" * 70)
            print(f"   未设置的变量: {', '.join(missing)}")
            print()
            print("   请通过以下任一方式配置：")
            print("   1. 创建 .env 文件（参考 .env.example）")
            print("   2. 在 docker-compose.yml 的 environment 中设置")
            print("   3. 直接设置系统环境变量")
            print()
            print("   示例 docker-compose.yml 配置：")
            print("     environment:")
            print("       - DB_HOST=postgres")
            print("       - DB_PORT=5432")
            print("       - DB_USER=postgres")
            print("       - DB_PASSWORD=your_password")
            print("       - DB_NAME=fast_blog")
            print("       - SECRET_KEY=your-secret-key-at-least-32-chars")
            print("=" * 70)
            print("   应用将继续启动，请通过 /install 页面完成数据库配置。")
            print("=" * 70)
        else:
            # 警告：未设置密码（允许，但提示安全风险）
            if not self.db_password:
                print("⚠️  警告：未设置 DB_PASSWORD，数据库将使用空密码连接")


class DevelopmentConfig(AppConfig):
    """开发环境配置"""

    def __init__(self):
        super().__init__()
        self.DEBUG = True
        self.TESTING = False


class TestingConfig(AppConfig):
    """测试环境配置"""

    def __init__(self):
        super().__init__()
        self.DEBUG = True
        self.TESTING = True


def get_config_by_env(env):
    """根据环境参数获取配置类"""
    # 支持简写和完整形式
    if env in ['prod', 'production']:
        return ProductionConfig()
    elif env in ['dev', 'development']:
        return DevelopmentConfig()
    elif env in ['test', 'testing']:
        return TestingConfig()
    else:
        return ProductionConfig()  # 默认使用生产环境配置
