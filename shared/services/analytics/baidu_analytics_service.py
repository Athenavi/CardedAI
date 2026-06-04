"""
百度统计集成服务

功能：
1. 百度统计配置管理
2. 追踪代码生成
3. 数据同步（可选）
"""

from typing import Optional, Dict, Any, List

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from shared.models.baidu_analytics_config import BaiduAnalyticsConfig

from src.unified_logger import default_logger as logger


class BaiduAnalyticsService:
    """
    百度统计集成服务
    
    支持百度统计 (Baidu Tongji)
    """

    def __init__(self):
        pass

    async def get_config(self, db: AsyncSession, site_id: Optional[int] = None) -> Optional[BaiduAnalyticsConfig]:
        """
        获取百度统计配置
        
        Args:
            db: 数据库会话
            site_id: 站点 ID（可选，为空则获取全局配置）
            
        Returns:
            百度统计配置对象
        """
        query = select(BaiduAnalyticsConfig).where(
            BaiduAnalyticsConfig.is_active == True
        )

        if site_id:
            query = query.where(BaiduAnalyticsConfig.site_id == site_id)
        else:
            query = query.where(BaiduAnalyticsConfig.site_id.is_(None))

        result = await db.execute(query)
        config = result.scalar_one_or_none()

        return config

    async def create_config(
            self,
            db: AsyncSession,
            site_token: str,
            api_key: Optional[str] = None,
            site_id: Optional[int] = None,
            enable_tracking: bool = True,
            enable_data_sync: bool = False,
    ) -> BaiduAnalyticsConfig:
        """
        创建百度统计配置
        
        Args:
            db: 数据库会话
            site_token: 百度统计 Site Token
            api_key: 百度统计 API Key
            site_id: 站点 ID（可选）
            enable_tracking: 是否启用追踪
            enable_data_sync: 是否启用数据同步
            
        Returns:
            创建的配置对象
        """
        # 检查是否已存在配置
        existing = await self.get_config(db, site_id)
        if existing:
            raise ValueError("Baidu Analytics configuration already exists for this scope")

        config = BaiduAnalyticsConfig(
            site_id=site_id,
            site_token=site_token,
            api_key=api_key,
            enable_tracking=enable_tracking,
            enable_data_sync=enable_data_sync,
            is_active=True,
        )

        db.add(config)
        await db.commit()
        await db.refresh(config)

        logger.info(f"Baidu Analytics config created for site {site_id}")
        return config

    async def update_config(
            self,
            db: AsyncSession,
            config_id: int,
            updates: Dict[str, Any],
    ) -> BaiduAnalyticsConfig:
        """
        更新百度统计配置
        
        Args:
            db: 数据库会话
            config_id: 配置 ID
            updates: 更新字段字典
            
        Returns:
            更新后的配置对象
        """
        config = await db.get(BaiduAnalyticsConfig, config_id)
        if not config:
            raise ValueError("Baidu Analytics configuration not found")

        for key, value in updates.items():
            if hasattr(config, key):
                setattr(config, key, value)

        await db.commit()
        await db.refresh(config)

        logger.info(f"Baidu Analytics config {config_id} updated")
        return config

    async def deactivate_config(self, db: AsyncSession, config_id: int):
        """
        停用百度统计配置
        
        Args:
            db: 数据库会话
            config_id: 配置 ID
        """
        config = await db.get(BaiduAnalyticsConfig, config_id)
        if not config:
            raise ValueError("Baidu Analytics configuration not found")

        config.is_active = False
        await db.commit()

        logger.info(f"Baidu Analytics config {config_id} deactivated")

    def generate_tracking_code(self, config: BaiduAnalyticsConfig) -> str:
        """
        生成百度统计追踪代码
        
        Args:
            config: 百度统计配置对象
            
        Returns:
            HTML/JavaScript 追踪代码
        """
        if not config.site_token:
            return ""

        tracking_code = """<!-- Baidu Analytics -->
<script>
var _hmt = _hmt || [];
(function() {{
  var hm = document.createElement("script");
  hm.src = "https://hm.baidu.com/hm.js?{site_token}";
  var s = document.getElementsByTagName("script")[0]; 
  s.parentNode.insertBefore(hm, s);
}})();
</script>
<!-- End Baidu Analytics -->""".format(site_token=config.site_token)

        return tracking_code

    async def get_all_configs(self, db: AsyncSession, include_inactive: bool = False) -> List[BaiduAnalyticsConfig]:
        """
        获取所有百度统计配置
        
        Args:
            db: 数据库会话
            include_inactive: 是否包含非活动配置
            
        Returns:
            配置列表
        """
        query = select(BaiduAnalyticsConfig)

        if not include_inactive:
            query = query.where(BaiduAnalyticsConfig.is_active == True)

        result = await db.execute(query)
        return result.scalars().all()


# 全局实例
baidu_analytics_service = BaiduAnalyticsService()
