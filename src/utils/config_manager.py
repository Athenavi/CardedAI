"""
配置管理器，用于动态更新和刷新系统配置
"""
import json
from typing import Dict, Any

from sqlalchemy.orm import Session

from shared.models import SystemSettings
from src.utils.storage.s3_storage import s3_storage


class ConfigManager:
    def __init__(self):
        # 在FastAPI环境中，邮件配置的处理方式可能需要调整
        self.s3_storage = s3_storage
        self._app_config = None  # 延迟加载app_config以避免循环导入

    @property
    def app_config(self):
        if self._app_config is None:
            from src.setting import app_config
            self._app_config = app_config
        return self._app_config

    @staticmethod
    def load_config_from_db(db: Session) -> Dict[str, Any]:
        """从数据库加载配置"""
        from sqlalchemy import select
        settings_query = select(SystemSettings)
        settings_result = db.execute(settings_query)
        settings = settings_result.scalars().all()
        config = {}
        for setting in settings:
            if setting.value is None:
                config[setting.key] = None
            else:
                try:
                    # 尝试将值反序列化为JSON对象
                    config[setting.key] = json.loads(setting.value)
                except (json.JSONDecodeError, TypeError):
                    # 如果不是JSON格式，则直接使用原始值
                    config[setting.key] = setting.value
        return config

    def refresh_mail_config(self, db: Session, app_config=None):
        """刷新邮件配置"""
        # 从数据库加载邮件配置
        config = self.load_config_from_db(db)

        # 获取邮件配置
        mail_host = config.get('mail_host')
        mail_port = config.get('mail_port')
        mail_user = config.get('mail_user')
        mail_password = config.get('mail_password')
        mail_from = config.get('mail_from')  # 从数据库获取发件人地址

        # 返回配置字典，由调用方处理邮件配置的更新
        mail_config = {}
        if mail_host:
            mail_config['MAIL_SERVER'] = mail_host
        if mail_port:
            mail_config['MAIL_PORT'] = int(mail_port) if isinstance(mail_port, (int, str)) else 587
        if mail_user:
            mail_config['MAIL_USERNAME'] = mail_user
        if mail_password:
            mail_config['MAIL_PASSWORD'] = mail_password
        if mail_from:
            mail_config['MAIL_FROM_ADDRESS'] = mail_from  # 添加发件人地址配置

        # 使用STARTTLS而不是SSL
        mail_config['MAIL_USE_TLS'] = True
        mail_config['MAIL_USE_SSL'] = False
        mail_config['MAIL_DEFAULT_SENDER'] = mail_user or mail_from

        # 如果提供了app_config，更新它的属性；否则使用属性
        if app_config:
            for key, value in mail_config.items():
                setattr(app_config, key, value)
        else:
            # 使用延迟加载的app_config
            actual_app_config = self.app_config
            for key, value in mail_config.items():
                setattr(actual_app_config, key, value)

        return mail_config

    def refresh_s3_config(self, db: Session):
        """刷新S3配置"""
        try:
            config = self.load_config_from_db(db)

            # 获取S3配置
            s3_enabled = config.get('s3_enabled', True)
            s3_endpoint = config.get('s3_endpoint')
            s3_access_key = config.get('s3_access_key')
            s3_secret_key = config.get('s3_secret_key')
            s3_bucket_name = config.get('s3_bucket', 'media-bucket')
            s3_region = config.get('s3_region', 'us-east-1')
            s3_use_ssl = config.get('s3_use_ssl', True)

            # 返回配置字典，由调用方处理S3配置的更新
            s3_config = {
                'S3_ENABLED': s3_enabled,
                'S3_ENDPOINT_URL': s3_endpoint,
                'S3_ACCESS_KEY': s3_access_key,
                'S3_SECRET_KEY': s3_secret_key,
                'S3_BUCKET_NAME': s3_bucket_name,
                'S3_REGION': s3_region,
                'S3_USE_SSL': s3_use_ssl
            }

            return s3_config
        except Exception as e:
            print(f"S3配置刷新失败: {e}")
            return {}

    def refresh_all_configs(self, db: Session):
        """刷新所有配置"""
        print("开始刷新所有配置...")

        mail_config = self.refresh_mail_config(db, self.app_config)
        s3_config = self.refresh_s3_config(db)

        print("所有配置已刷新完成")

        return {
            'mail_config': mail_config,
            's3_config': s3_config
        }


# 创建全局配置管理器实例
config_manager = ConfigManager()
