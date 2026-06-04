"""
企业版服务模块
提供许可证管理、技术支持、SLA保障等功能
"""
import uuid
from datetime import datetime, timedelta
from typing import Optional, Dict, Any, List

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from shared.models.enterprise_license import EnterpriseLicense
from shared.models.support_ticket import SupportTicket
from shared.models.support_ticket_reply import SupportTicketReply
from shared.models.deployment_script import DeploymentScript
from shared.models.deployment_log import DeploymentLog
from shared.models.monitoring_alert import MonitoringAlert
from shared.models.monitoring_metric import MonitoringMetric

from src.unified_logger import default_logger as logger


class EnterpriseService:
    """
    企业版服务
    
    功能：
    1. 许可证管理
    2. 优先技术支持
    3. SLA保障
    4. 部署脚本管理
    5. 监控告警
    """

    async def create_license(
            self,
            db: AsyncSession,
            license_type: str = 'professional',
            company_name: str = '',
            contact_email: str = '',
            max_sites: int = -1,
            features: Dict = None,
            valid_days: int = 365,
            support_level: str = 'standard',
            sla_enabled: bool = False,
            sla_uptime_guarantee: float = 99.9
    ) -> EnterpriseLicense:
        """
        创建企业许可证
        
        Args:
            db: 数据库会话
            license_type: 许可证类型
            company_name: 公司名称
            contact_email: 联系邮箱
            max_sites: 最大站点数（-1表示无限）
            features: 功能列表
            valid_days: 有效天数
            support_level: 支持级别
            sla_enabled: 是否启用SLA
            sla_uptime_guarantee: SLA可用性保证
            
        Returns:
            创建的许可证
        """
        # 生成许可证密钥
        license_key = f"FB-{license_type.upper()}-{uuid.uuid4().hex[:16].upper()}"

        valid_from = datetime.now()
        valid_until = valid_from + timedelta(days=valid_days) if valid_days > 0 else None

        license_obj = EnterpriseLicense(
            license_key=license_key,
            license_type=license_type,
            company_name=company_name,
            contact_email=contact_email,
            max_sites=max_sites,
            features=str(features) if features else None,
            valid_from=valid_from,
            valid_until=valid_until,
            support_level=support_level,
            sla_enabled=sla_enabled,
            sla_uptime_guarantee=sla_uptime_guarantee if sla_enabled else None
        )

        db.add(license_obj)
        await db.commit()
        await db.refresh(license_obj)

        logger.info(f"Enterprise license created: {license_key}")
        return license_obj

    async def validate_license(self, db: AsyncSession, license_key: str) -> Optional[EnterpriseLicense]:
        """
        验证许可证
        
        Args:
            db: 数据库会话
            license_key: 许可证密钥
            
        Returns:
            许可证对象，如果无效则返回None
        """
        stmt = select(EnterpriseLicense).where(
            EnterpriseLicense.license_key == license_key,
            EnterpriseLicense.is_active == True
        )
        result = await db.execute(stmt)
        license_obj = result.scalar_one_or_none()

        if not license_obj:
            return None

        # 检查是否过期
        if license_obj.valid_until and license_obj.valid_until < datetime.now():
            logger.warning(f"License expired: {license_key}")
            return None

        return license_obj

    async def get_license_info(self, db: AsyncSession, license_key: str) -> Optional[Dict[str, Any]]:
        """
        获取许可证信息
        
        Args:
            db: 数据库会话
            license_key: 许可证密钥
            
        Returns:
            许可证信息字典
        """
        license_obj = await self.validate_license(db, license_key)
        if not license_obj:
            return None

        return {
            'license_key': license_obj.license_key,
            'license_type': license_obj.license_type,
            'company_name': license_obj.company_name,
            'contact_email': license_obj.contact_email,
            'max_sites': license_obj.max_sites,
            'features': license_obj.features,
            'valid_from': license_obj.valid_from.isoformat() if license_obj.valid_from else None,
            'valid_until': license_obj.valid_until.isoformat() if license_obj.valid_until else None,
            'support_level': license_obj.support_level,
            'sla_enabled': license_obj.sla_enabled,
            'sla_uptime_guarantee': license_obj.sla_uptime_guarantee,
            'is_active': license_obj.is_active
        }

    async def create_support_ticket(
            self,
            db: AsyncSession,
            user_id: int,
            subject: str,
            description: str,
            priority: str = 'medium',
            category: str = 'general',
            license_id: Optional[int] = None
    ) -> SupportTicket:
        """
        创建技术支持工单
        
        Args:
            db: 数据库会话
            user_id: 用户ID
            subject: 主题
            description: 描述
            priority: 优先级
            category: 分类
            license_id: 许可证ID
            
        Returns:
            创建的工单
        """
        # 生成工单编号
        ticket_number = f"TKT-{datetime.now().strftime('%Y%m%d')}-{uuid.uuid4().hex[:8].upper()}"

        ticket = SupportTicket(
            ticket_number=ticket_number,
            user_id=user_id,
            license_id=license_id,
            subject=subject,
            description=description,
            priority=priority,
            category=category
        )

        db.add(ticket)
        await db.commit()
        await db.refresh(ticket)

        logger.info(f"Support ticket created: {ticket_number}")
        return ticket

    async def add_ticket_reply(
            self,
            db: AsyncSession,
            ticket_id: int,
            user_id: int,
            content: str,
            is_staff: bool = False,
            attachments: List[str] = None
    ) -> SupportTicketReply:
        """
        添加工单回复
        
        Args:
            db: 数据库会话
            ticket_id: 工单ID
            user_id: 用户ID
            content: 回复内容
            is_staff: 是否为工作人员
            attachments: 附件列表
            
        Returns:
            创建的回复
        """
        reply = SupportTicketReply(
            ticket_id=ticket_id,
            user_id=user_id,
            content=content,
            is_staff=is_staff,
            attachments=str(attachments) if attachments else None
        )

        db.add(reply)

        # 更新工单状态
        if is_staff:
            stmt = select(SupportTicket).where(SupportTicket.id == ticket_id)
            result = await db.execute(stmt)
            ticket = result.scalar_one_or_none()
            if ticket and ticket.status == 'open':
                ticket.status = 'in_progress'

        await db.commit()
        await db.refresh(reply)

        return reply

    async def get_user_tickets(
            self,
            db: AsyncSession,
            user_id: int,
            status: Optional[str] = None
    ) -> List[SupportTicket]:
        """
        获取用户的工单列表
        
        Args:
            db: 数据库会话
            user_id: 用户ID
            status: 状态过滤
            
        Returns:
            工单列表
        """
        stmt = select(SupportTicket).where(SupportTicket.user_id == user_id)

        if status:
            stmt = stmt.where(SupportTicket.status == status)

        stmt = stmt.order_by(SupportTicket.created_at.desc())

        result = await db.execute(stmt)
        return result.scalars().all()

    async def create_deployment_script(
            self,
            db: AsyncSession,
            name: str,
            script_type: str,
            content: str,
            version: str = '1.0.0',
            description: str = None,
            parameters: Dict = None,
            created_by: Optional[int] = None
    ) -> DeploymentScript:
        """
        创建部署脚本
        
        Args:
            db: 数据库会话
            name: 脚本名称
            script_type: 脚本类型
            content: 脚本内容
            version: 版本
            description: 描述
            parameters: 参数定义
            created_by: 创建者ID
            
        Returns:
            创建的脚本
        """
        script = DeploymentScript(
            name=name,
            script_type=script_type,
            content=content,
            version=version,
            description=description,
            parameters=str(parameters) if parameters else None,
            created_by=created_by
        )

        db.add(script)
        await db.commit()
        await db.refresh(script)

        logger.info(f"Deployment script created: {name} (v{version})")
        return script

    async def execute_deployment_script(
            self,
            db: AsyncSession,
            script_id: int,
            user_id: Optional[int] = None
    ) -> DeploymentLog:
        """
        执行部署脚本
        
        Args:
            db: 数据库会话
            script_id: 脚本ID
            user_id: 执行者ID
            
        Returns:
            部署日志
        """
        # 创建日志记录
        log = DeploymentLog(
            script_id=script_id,
            user_id=user_id,
            status='running',
            started_at=datetime.now()
        )

        db.add(log)
        await db.commit()
        await db.refresh(log)

        # 执行脚本（简化版本，实际生产环境需要更复杂的异步执行逻辑）
        try:
            import subprocess
            result = subprocess.run(
                ['bash', '-c', script.content],
                capture_output=True,
                text=True,
                timeout=300
            )

            log.output = result.stdout
            if result.returncode != 0:
                log.status = 'failed'
                log.error_message = result.stderr
            else:
                log.status = 'success'

            log.completed_at = datetime.now()
            await db.commit()
        except Exception as e:
            log.status = 'failed'
            log.error_message = str(e)
            log.completed_at = datetime.now()
            await db.commit()

        return log

    async def create_monitoring_alert(
            self,
            db: AsyncSession,
            alert_type: str,
            severity: str,
            title: str,
            message: str,
            source: str = None,
            metric_name: str = None,
            metric_value: float = None,
            threshold: float = None
    ) -> MonitoringAlert:
        """
        创建监控告警
        
        Args:
            db: 数据库会话
            alert_type: 告警类型
            severity: 严重程度
            title: 标题
            message: 消息
            source: 来源
            metric_name: 指标名称
            metric_value: 指标值
            threshold: 阈值
            
        Returns:
            创建的告警
        """
        alert = MonitoringAlert(
            alert_type=alert_type,
            severity=severity,
            title=title,
            message=message,
            source=source,
            metric_name=metric_name,
            metric_value=metric_value,
            threshold=threshold
        )

        db.add(alert)
        await db.commit()
        await db.refresh(alert)

        logger.warning(f"Monitoring alert created: {title} ({severity})")
        return alert

    async def record_monitoring_metric(
            self,
            db: AsyncSession,
            metric_name: str,
            metric_value: float,
            metric_type: str,
            labels: Dict = None,
            site_id: Optional[int] = None
    ) -> MonitoringMetric:
        """
        记录监控指标
        
        Args:
            db: 数据库会话
            metric_name: 指标名称
            metric_value: 指标值
            metric_type: 指标类型
            labels: 标签
            site_id: 站点ID
            
        Returns:
            创建的指标记录
        """
        metric = MonitoringMetric(
            metric_name=metric_name,
            metric_value=metric_value,
            metric_type=metric_type,
            labels=str(labels) if labels else None,
            timestamp=datetime.now(),
            site_id=site_id
        )

        db.add(metric)
        await db.commit()
        await db.refresh(metric)

        return metric


# 全局实例
enterprise_service = EnterpriseService()
