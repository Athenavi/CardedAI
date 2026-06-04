"""
Google Analytics 集成服务

功能：
1. Google Analytics 配置管理
2. 页面浏览追踪代码生成
3. 事件追踪支持
4. 用户行为分析
5. 数据同步（可选）
"""

from typing import Optional, Dict, Any, List

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from shared.models.google_analytics_config import GoogleAnalyticsConfig

from src.unified_logger import default_logger as logger


class GoogleAnalyticsService:
    """
    Google Analytics 集成服务
    
    支持 GA4 (Google Analytics 4)
    """

    def __init__(self):
        pass

    async def get_config(self, db: AsyncSession, site_id: Optional[int] = None) -> Optional[GoogleAnalyticsConfig]:
        """
        获取 Google Analytics 配置
        
        Args:
            db: 数据库会话
            site_id: 站点 ID（可选，为空则获取全局配置）
            
        Returns:
            Google Analytics 配置对象
        """
        query = select(GoogleAnalyticsConfig).where(
            GoogleAnalyticsConfig.is_active == True
        )

        if site_id:
            query = query.where(GoogleAnalyticsConfig.site_id == site_id)
        else:
            query = query.where(GoogleAnalyticsConfig.site_id.is_(None))

        result = await db.execute(query)
        config = result.scalar_one_or_none()

        return config

    async def create_config(
            self,
            db: AsyncSession,
            tracking_id: str,
            measurement_id: Optional[str] = None,
            api_secret: Optional[str] = None,
            site_id: Optional[int] = None,
            enable_page_view_tracking: bool = True,
            enable_event_tracking: bool = True,
            enable_user_behavior_analysis: bool = False,
            anonymize_ip: bool = True,
            sample_rate: float = 100.0,
    ) -> GoogleAnalyticsConfig:
        """
        创建 Google Analytics 配置
        
        Args:
            db: 数据库会话
            tracking_id: Tracking ID (如 G-XXXXXXXXXX)
            measurement_id: GA4 Measurement ID
            api_secret: API Secret
            site_id: 站点 ID（可选）
            enable_page_view_tracking: 是否启用页面浏览追踪
            enable_event_tracking: 是否启用事件追踪
            enable_user_behavior_analysis: 是否启用用户行为分析
            anonymize_ip: 是否匿名化 IP
            sample_rate: 采样率（0-100）
            
        Returns:
            创建的配置对象
        """
        # 检查是否已存在配置
        existing = await self.get_config(db, site_id)
        if existing:
            raise ValueError("Google Analytics configuration already exists for this scope")

        config = GoogleAnalyticsConfig(
            site_id=site_id,
            tracking_id=tracking_id,
            measurement_id=measurement_id,
            api_secret=api_secret,
            enable_page_view_tracking=enable_page_view_tracking,
            enable_event_tracking=enable_event_tracking,
            enable_user_behavior_analysis=enable_user_behavior_analysis,
            anonymize_ip=anonymize_ip,
            sample_rate=sample_rate,
            is_active=True,
        )

        db.add(config)
        await db.commit()
        await db.refresh(config)

        logger.info(f"Google Analytics config created for site {site_id}")
        return config

    async def update_config(
            self,
            db: AsyncSession,
            config_id: int,
            updates: Dict[str, Any],
    ) -> GoogleAnalyticsConfig:
        """
        更新 Google Analytics 配置
        
        Args:
            db: 数据库会话
            config_id: 配置 ID
            updates: 更新字段字典
            
        Returns:
            更新后的配置对象
        """
        config = await db.get(GoogleAnalyticsConfig, config_id)
        if not config:
            raise ValueError("Google Analytics configuration not found")

        for key, value in updates.items():
            if hasattr(config, key):
                setattr(config, key, value)

        await db.commit()
        await db.refresh(config)

        logger.info(f"Google Analytics config {config_id} updated")
        return config

    async def deactivate_config(self, db: AsyncSession, config_id: int):
        """
        停用 Google Analytics 配置
        
        Args:
            db: 数据库会话
            config_id: 配置 ID
        """
        config = await db.get(GoogleAnalyticsConfig, config_id)
        if not config:
            raise ValueError("Google Analytics configuration not found")

        config.is_active = False
        await db.commit()

        logger.info(f"Google Analytics config {config_id} deactivated")

    def generate_tracking_code(self, config: GoogleAnalyticsConfig) -> str:
        """
        生成 Google Analytics 追踪代码
        
        Args:
            config: Google Analytics 配置对象
            
        Returns:
            HTML/JavaScript 追踪代码
        """
        if not config.tracking_id and not config.measurement_id:
            return ""

        # 使用 Measurement ID（GA4）
        measurement_id = config.measurement_id or config.tracking_id

        # 构建配置选项
        options = []

        if config.anonymize_ip:
            options.append("gtag('config', '{}', {{ 'anonymize_ip': true }});".format(measurement_id))
        else:
            options.append("gtag('config', '{}');".format(measurement_id))

        if config.sample_rate < 100.0:
            options[-1] = options[-1].replace(
                ");",
                ", {{ 'sample_rate': {} }});".format(config.sample_rate)
            )

        tracking_code = """<!-- Google Analytics 4 -->
<script async src="https://www.googletagmanager.com/gtag/js?id={measurement_id}"></script>
<script>
  window.dataLayer = window.dataLayer || [];
  function gtag(){{dataLayer.push(arguments);}}
  gtag('js', new Date());
  {options}
</script>
<!-- End Google Analytics 4 -->""".format(
            measurement_id=measurement_id,
            options='\n  '.join(options)
        )

        return tracking_code

    def generate_event_tracking_code(self, event_name: str, event_params: Dict[str, Any] = None) -> str:
        """
        生成事件追踪代码
        
        Args:
            event_name: 事件名称
            event_params: 事件参数
            
        Returns:
            JavaScript 事件追踪代码
        """
        params_str = ""
        if event_params:
            import json
            params_str = ", " + json.dumps(event_params)

        event_code = "gtag('event', '{}'{});".format(event_name, params_str)
        return event_code

    async def get_all_configs(self, db: AsyncSession, include_inactive: bool = False) -> List[GoogleAnalyticsConfig]:
        """
        获取所有 Google Analytics 配置
        
        Args:
            db: 数据库会话
            include_inactive: 是否包含非活动配置
            
        Returns:
            配置列表
        """
        query = select(GoogleAnalyticsConfig)

        if not include_inactive:
            query = query.where(GoogleAnalyticsConfig.is_active == True)

        result = await db.execute(query)
        return result.scalars().all()


# 全局实例
google_analytics_service = GoogleAnalyticsService()
