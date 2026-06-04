"""
专家认证系统服务
提供领域专家申请、审核、认证标识等功能
"""


from collections import defaultdict
from datetime import datetime, timedelta
from typing import Dict, List, Optional

from src.unified_logger import default_logger as logger


class ExpertCertificationSystem:
    """专家认证系统"""

    def __init__(self):
        # 认证领域定义
        self._certification_fields = {
            'programming': {
                'name': '编程开发',
                'description': '软件工程、编程语言、框架等',
                'icon': '💻',
            },
            'ai_ml': {
                'name': '人工智能',
                'description': '机器学习、深度学习、NLP等',
                'icon': '🤖',
            },
            'data_science': {
                'name': '数据科学',
                'description': '数据分析、数据挖掘、可视化等',
                'icon': '📊',
            },
            'cloud_devops': {
                'name': '云计算/DevOps',
                'description': '云平台、容器化、自动化运维等',
                'icon': '☁️',
            },
            'mobile_dev': {
                'name': '移动开发',
                'description': 'iOS、Android、跨平台开发等',
                'icon': '📱',
            },
            'web_frontend': {
                'name': 'Web前端',
                'description': 'HTML/CSS/JavaScript、框架等',
                'icon': '🌐',
            },
            'backend_arch': {
                'name': '后端架构',
                'description': '微服务、分布式系统、数据库等',
                'icon': '⚙️',
            },
            'security': {
                'name': '网络安全',
                'description': '信息安全、渗透测试、加密技术等',
                'icon': '🔒',
            },
            'blockchain': {
                'name': '区块链',
                'description': '智能合约、DeFi、Web3等',
                'icon': '⛓️',
            },
            'product_management': {
                'name': '产品管理',
                'description': '产品设计、项目管理、用户体验等',
                'icon': '📋',
            },
        }

        # 认证申请 {application_id: application_info}
        self._applications = {}

        # 用户认证状态 {user_id: certification_info}
        self._certifications = {}

        # 申请ID计数器
        self._app_counter = 0

    def apply_certification(self, user_id: int, field_id: str,
                            credentials: Dict, bio: str = '') -> str:
        """
        提交专家认证申请
        
        Args:
            user_id: 用户ID
            field_id: 认证领域ID
            credentials: 资质证明(学历/工作经历/作品等)
            bio: 个人简介
            
        Returns:
            申请ID
        """
        if field_id not in self._certification_fields:
            raise ValueError(f"Invalid field_id: {field_id}")

        # 检查是否已认证
        if user_id in self._certifications:
            existing_cert = self._certifications[user_id]
            if existing_cert['field_id'] == field_id and existing_cert['status'] == 'approved':
                raise ValueError("Already certified in this field")

        # 生成申请ID
        self._app_counter += 1
        app_id = f"app_{self._app_counter}_{int(datetime.now().timestamp())}"

        now = datetime.now()
        application = {
            'application_id': app_id,
            'user_id': user_id,
            'field_id': field_id,
            'credentials': credentials,
            'bio': bio,
            'status': 'pending',  # pending/approved/rejected
            'submitted_at': now,
            'reviewed_at': None,
            'reviewer_id': None,
            'rejection_reason': None,
        }

        self._applications[app_id] = application

        logger.info(f"User {user_id} applied for certification in {field_id}")
        return app_id

    def review_application(self, application_id: str, reviewer_id: int,
                           approved: bool, rejection_reason: str = None) -> bool:
        """
        审核认证申请
        
        Args:
            application_id: 申请ID
            reviewer_id: 审核员ID
            approved: 是否通过
            rejection_reason: 拒绝原因(拒绝时必需)
            
        Returns:
            是否成功
        """
        app = self._applications.get(application_id)

        if not app:
            return False

        if app['status'] != 'pending':
            return False

        now = datetime.now()

        # 更新申请状态
        app['status'] = 'approved' if approved else 'rejected'
        app['reviewed_at'] = now
        app['reviewer_id'] = reviewer_id

        if not approved:
            if not rejection_reason:
                return False
            app['rejection_reason'] = rejection_reason

        # 如果通过，创建认证记录
        if approved:
            self._certifications[app['user_id']] = {
                'user_id': app['user_id'],
                'field_id': app['field_id'],
                'status': 'approved',
                'certified_at': now,
                'expires_at': now + timedelta(days=365 * 2),  # 2年有效期
                'bio': app['bio'],
                'credentials': app['credentials'],
            }

        logger.info(f"Application {application_id} {'approved' if approved else 'rejected'} by reviewer {reviewer_id}")
        return True

    def get_user_certification(self, user_id: int) -> Optional[Dict]:
        """
        获取用户认证信息
        
        Args:
            user_id: 用户ID
            
        Returns:
            认证信息
        """
        cert = self._certifications.get(user_id)

        if not cert:
            return None

        # 检查是否过期
        if cert['expires_at'] < datetime.now():
            cert['status'] = 'expired'

        field_info = self._certification_fields.get(cert['field_id'], {})

        return {
            **cert,
            'field_name': field_info.get('name', ''),
            'field_icon': field_info.get('icon', ''),
            'is_valid': cert['status'] == 'approved' and cert['expires_at'] > datetime.now(),
        }

    def is_expert(self, user_id: int, field_id: str = None) -> bool:
        """
        检查用户是否是专家
        
        Args:
            user_id: 用户ID
            field_id: 领域ID(可选，不指定则检查任意领域)
            
        Returns:
            是否是专家
        """
        cert = self._certifications.get(user_id)

        if not cert:
            return False

        # 检查状态和有效期
        if cert['status'] != 'approved':
            return False
        if cert['expires_at'] < datetime.now():
            return False

        # 如果指定了领域，检查是否匹配
        if field_id and cert['field_id'] != field_id:
            return False

        return True

    def get_pending_applications(self, field_id: str = None) -> List[Dict]:
        """
        获取待审核的申请列表
        
        Args:
            field_id: 领域过滤(可选)
            
        Returns:
            申请列表
        """
        applications = []

        for app in self._applications.values():
            if app['status'] != 'pending':
                continue

            if field_id and app['field_id'] != field_id:
                continue

            field_info = self._certification_fields.get(app['field_id'], {})

            applications.append({
                'application_id': app['application_id'],
                'user_id': app['user_id'],
                'field_id': app['field_id'],
                'field_name': field_info.get('name', ''),
                'field_icon': field_info.get('icon', ''),
                'credentials': app['credentials'],
                'bio': app['bio'],
                'submitted_at': app['submitted_at'].isoformat(),
            })

        # 按提交时间排序
        applications.sort(key=lambda x: x['submitted_at'], reverse=True)

        return applications

    def get_application_details(self, application_id: str) -> Optional[Dict]:
        """
        获取申请详情
        
        Args:
            application_id: 申请ID
            
        Returns:
            申请详情
        """
        app = self._applications.get(application_id)

        if not app:
            return None

        field_info = self._certification_fields.get(app['field_id'], {})

        return {
            **app,
            'field_name': field_info.get('name', ''),
            'field_icon': field_info.get('icon', ''),
            'submitted_at': app['submitted_at'].isoformat(),
            'reviewed_at': app['reviewed_at'].isoformat() if app['reviewed_at'] else None,
        }

    def get_certified_experts(self, field_id: str = None,
                              limit: int = 100) -> List[Dict]:
        """
        获取已认证的专家列表
        
        Args:
            field_id: 领域过滤(可选)
            limit: 返回数量
            
        Returns:
            专家列表
        """
        experts = []

        for cert in self._certifications.values():
            if cert['status'] != 'approved':
                continue
            if cert['expires_at'] < datetime.now():
                continue

            if field_id and cert['field_id'] != field_id:
                continue

            field_info = self._certification_fields.get(cert['field_id'], {})

            experts.append({
                'user_id': cert['user_id'],
                'field_id': cert['field_id'],
                'field_name': field_info.get('name', ''),
                'field_icon': field_info.get('icon', ''),
                'bio': cert['bio'],
                'certified_at': cert['certified_at'].isoformat(),
                'expires_at': cert['expires_at'].isoformat(),
            })

        # 按认证时间排序(最新的在前)
        experts.sort(key=lambda x: x['certified_at'], reverse=True)

        return experts[:limit]

    def revoke_certification(self, user_id: int, reason: str = '') -> bool:
        """
        撤销专家认证(管理员操作)
        
        Args:
            user_id: 用户ID
            reason: 撤销原因
            
        Returns:
            是否成功
        """
        if user_id not in self._certifications:
            return False

        cert = self._certifications[user_id]
        cert['status'] = 'revoked'
        cert['revoked_at'] = datetime.now()
        cert['revocation_reason'] = reason

        logger.info(f"Certification revoked for user {user_id}: {reason}")
        return True

    def get_certification_stats(self) -> Dict:
        """
        获取认证系统统计
        
        Returns:
            统计数据
        """
        total_applications = len(self._applications)
        pending_count = len([a for a in self._applications.values() if a['status'] == 'pending'])
        approved_count = len([a for a in self._applications.values() if a['status'] == 'approved'])
        rejected_count = len([a for a in self._applications.values() if a['status'] == 'rejected'])

        active_experts = len([
            c for c in self._certifications.values()
            if c['status'] == 'approved' and c['expires_at'] > datetime.now()
        ])

        # 按领域统计
        field_distribution = defaultdict(int)
        for cert in self._certifications.values():
            if cert['status'] == 'approved' and cert['expires_at'] > datetime.now():
                field_distribution[cert['field_id']] += 1

        return {
            'total_applications': total_applications,
            'pending_applications': pending_count,
            'approved_applications': approved_count,
            'rejected_applications': rejected_count,
            'active_experts': active_experts,
            'field_distribution': dict(field_distribution),
        }

    def get_available_fields(self) -> List[Dict]:
        """
        获取可认证的领域列表
        
        Returns:
            领域列表
        """
        fields = []

        for field_id, field_info in self._certification_fields.items():
            # 统计该领域的专家数量
            expert_count = len([
                c for c in self._certifications.values()
                if c['field_id'] == field_id
                   and c['status'] == 'approved'
                   and c['expires_at'] > datetime.now()
            ])

            fields.append({
                'field_id': field_id,
                **field_info,
                'expert_count': expert_count,
            })

        return fields


# 全局实例
expert_certification_system = ExpertCertificationSystem()
