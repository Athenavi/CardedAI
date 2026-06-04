"""
A/B测试插件
A/B测试插件，支持页面元素、标题、按钮等多维度测试
"""

import hashlib
import time
from collections import defaultdict
from datetime import datetime
from typing import Dict, List, Any, Optional

from shared.services.plugins.plugin_manager.core import BasePlugin, plugin_hooks


class ABTestingPlugin(BasePlugin):
    """
    A/B测试插件
    
    功能:
    1. 创建A/B测试实验
    2. 流量分配管理
    3. 测试变体配置
    4. 转化率跟踪
    5. 统计分析报表
    6. 自动选择最优版本
    """

    def __init__(self):
        super().__init__(
            plugin_id=0,
            name="A/B测试",
            slug="ab-testing",
            version="1.0.0"
        )

        # 默认设置
        self.settings = {
            'enable_ab_testing': True,
            'default_traffic_split': 50,  # 默认流量分配百分比
            'tracking_method': 'cookie',  # cookie, session, ip
            'cookie_duration_days': 30,
            'auto_select_winner': False,  # 自动选择优胜者
            'confidence_level': 95,  # 置信度
            'min_sample_size': 100,  # 最小样本量
        }

        # 实验列表 {experiment_id: experiment_data}
        self.experiments: Dict[str, Dict[str, Any]] = {}

        # 用户分组 {user_id: {experiment_id: variant}}
        self.user_assignments: Dict[str, Dict[str, str]] = defaultdict(dict)

        # 转化数据 {experiment_id: {variant: {views, conversions}}}
        self.conversion_data: Dict[str, Dict[str, Dict[str, int]]] = defaultdict(
            lambda: defaultdict(lambda: {'views': 0, 'conversions': 0})
        )

    def register_hooks(self):
        """注册钩子"""
        # 页面加载时检查实验
        plugin_hooks.add_filter(
            "before_response",
            self.check_active_experiments,
            priority=5
        )

        # 转化事件追踪
        plugin_hooks.add_action(
            "conversion_event",
            self.track_conversion,
            priority=10
        )

    def activate(self):
        """激活插件"""
        super().activate()
        print("[ABTesting] Plugin activated")

    def deactivate(self):
        """停用插件"""
        super().deactivate()
        print("[ABTesting] Plugin deactivated")

    def create_experiment(self, experiment_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        创建A/B测试实验
        
        Args:
            experiment_data: 实验数据 {name, description, variants, traffic_split, goals}
            
        Returns:
            创建的实验
        """
        if not self.settings.get('enable_ab_testing'):
            raise Exception("A/B测试功能已禁用")

        # 生成ID
        experiment_id = f"exp_{int(time.time() * 1000)}"

        # 验证数据
        validation = self._validate_experiment(experiment_data)
        if not validation['valid']:
            raise ValueError(validation['error'])

        experiment = {
            'id': experiment_id,
            'name': experiment_data.get('name', ''),
            'description': experiment_data.get('description', ''),
            'status': 'draft',  # draft, running, paused, completed
            'variants': experiment_data.get('variants', []),
            'traffic_split': experiment_data.get('traffic_split', self.settings.get('default_traffic_split', 50)),
            'goals': experiment_data.get('goals', []),
            'target_pages': experiment_data.get('target_pages', []),
            'created_at': datetime.now().isoformat(),
            'started_at': None,
            'ended_at': None,
            'total_participants': 0,
        }

        self.experiments[experiment_id] = experiment

        print(f"[ABTesting] Created experiment: {experiment_id}")
        return experiment

    def start_experiment(self, experiment_id: str) -> bool:
        """启动实验"""
        if experiment_id not in self.experiments:
            return False

        experiment = self.experiments[experiment_id]
        
        if experiment['status'] != 'draft':
            return False

        experiment['status'] = 'running'
        experiment['started_at'] = datetime.now().isoformat()

        print(f"[ABTesting] Started experiment: {experiment_id}")
        return True

    def pause_experiment(self, experiment_id: str) -> bool:
        """暂停实验"""
        if experiment_id not in self.experiments:
            return False

        experiment = self.experiments[experiment_id]
        
        if experiment['status'] != 'running':
            return False

        experiment['status'] = 'paused'

        print(f"[ABTesting] Paused experiment: {experiment_id}")
        return True

    def stop_experiment(self, experiment_id: str) -> bool:
        """停止实验"""
        if experiment_id not in self.experiments:
            return False

        experiment = self.experiments[experiment_id]
        
        if experiment['status'] not in ['running', 'paused']:
            return False

        experiment['status'] = 'completed'
        experiment['ended_at'] = datetime.now().isoformat()

        # 自动选择优胜者
        if self.settings.get('auto_select_winner'):
            winner = self._determine_winner(experiment_id)
            if winner:
                experiment['winner'] = winner

        print(f"[ABTesting] Stopped experiment: {experiment_id}")
        return True

    def check_active_experiments(self, request_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        检查活跃的实验
        
        Args:
            request_data: 请求数据 {url, user_id, ip}
            
        Returns:
            实验分配结果
        """
        if not self.settings.get('enable_ab_testing'):
            return {}

        user_id = request_data.get('user_id') or request_data.get('ip', '')
        url = request_data.get('url', '')

        active_experiments = {}

        for exp_id, experiment in self.experiments.items():
            if experiment['status'] != 'running':
                continue

            # 检查是否匹配目标页面
            if experiment.get('target_pages'):
                if not any(url.startswith(page) for page in experiment['target_pages']):
                    continue

            # 分配用户到变体
            variant = self._assign_variant(exp_id, user_id)
            
            if variant:
                active_experiments[exp_id] = {
                    'experiment_id': exp_id,
                    'variant': variant,
                    'name': experiment['name'],
                }

                # 记录浏览
                self._record_view(exp_id, variant)

        return active_experiments if active_experiments else {}

    def track_conversion(self, conversion_data: Dict[str, Any]):
        """
        追踪转化事件
        
        Args:
            conversion_data: 转化数据 {experiment_id, variant, user_id, goal}
        """
        experiment_id = conversion_data.get('experiment_id')
        variant = conversion_data.get('variant')
        user_id = conversion_data.get('user_id')

        if not experiment_id or not variant:
            return

        # 记录转化
        self.conversion_data[experiment_id][variant]['conversions'] += 1

        print(f"[ABTesting] Conversion tracked: {experiment_id} - {variant}")

    def get_experiment_results(self, experiment_id: str) -> Optional[Dict[str, Any]]:
        """
        获取实验结果
        
        Args:
            experiment_id: 实验ID
            
        Returns:
            实验结果
        """
        if experiment_id not in self.experiments:
            return None

        experiment = self.experiments[experiment_id]
        results = {
            'experiment': experiment,
            'variants': [],
            'winner': None,
        }

        # 计算每个变体的数据
        for variant in experiment['variants']:
            variant_id = variant.get('id', '')
            data = self.conversion_data[experiment_id].get(variant_id, {'views': 0, 'conversions': 0})
            
            views = data['views']
            conversions = data['conversions']
            conversion_rate = (conversions / views * 100) if views > 0 else 0

            results['variants'].append({
                'variant': variant,
                'views': views,
                'conversions': conversions,
                'conversion_rate': round(conversion_rate, 2),
            })

        # 确定优胜者
        if experiment['status'] == 'completed':
            results['winner'] = experiment.get('winner')
        else:
            results['winner'] = self._determine_winner(experiment_id)

        return results

    def get_all_experiments(self, status: str = None) -> List[Dict[str, Any]]:
        """
        获取所有实验
        
        Args:
            status: 过滤状态
            
        Returns:
            实验列表
        """
        experiments = list(self.experiments.values())
        
        if status:
            experiments = [e for e in experiments if e['status'] == status]

        return experiments

    def _assign_variant(self, experiment_id: str, user_id: str) -> Optional[str]:
        """
        分配用户到变体
        
        Args:
            experiment_id: 实验ID
            user_id: 用户ID
            
        Returns:
            分配的变体ID
        """
        # 检查是否已有分配
        if user_id in self.user_assignments and experiment_id in self.user_assignments[user_id]:
            return self.user_assignments[user_id][experiment_id]

        experiment = self.experiments.get(experiment_id)
        if not experiment:
            return None

        variants = experiment.get('variants', [])
        if not variants:
            return None

        # 如果只有一个变体，直接返回
        if len(variants) == 1:
            variant_id = variants[0].get('id', 'control')
            self.user_assignments[user_id][experiment_id] = variant_id
            return variant_id

        # 使用哈希确保一致性
        hash_input = f"{experiment_id}:{user_id}"
        hash_value = int(hashlib.md5(hash_input.encode()).hexdigest(), 16)
        
        # 根据流量分配决定
        traffic_split = experiment.get('traffic_split', 50)
        
        if len(variants) == 2:
            # 简单的A/B测试
            variant_index = 0 if (hash_value % 100) < traffic_split else 1
        else:
            # 多变量测试
            variant_index = hash_value % len(variants)

        variant_id = variants[variant_index].get('id', f'variant_{variant_index}')
        
        # 保存分配
        self.user_assignments[user_id][experiment_id] = variant_id

        return variant_id

    def _record_view(self, experiment_id: str, variant: str):
        """记录浏览"""
        self.conversion_data[experiment_id][variant]['views'] += 1
        
        # 更新总参与人数
        if experiment_id in self.experiments:
            self.experiments[experiment_id]['total_participants'] += 1

    def _determine_winner(self, experiment_id: str) -> Optional[str]:
        """
        确定优胜者
        
        Args:
            experiment_id: 实验ID
            
        Returns:
            优胜者变体ID
        """
        if experiment_id not in self.experiments:
            return None

        experiment = self.experiments[experiment_id]
        variants_data = []

        for variant in experiment['variants']:
            variant_id = variant.get('id', '')
            data = self.conversion_data[experiment_id].get(variant_id, {'views': 0, 'conversions': 0})
            
            views = data['views']
            conversions = data['conversions']
            
            # 检查最小样本量
            min_sample = self.settings.get('min_sample_size', 100)
            if views < min_sample:
                return None

            conversion_rate = conversions / views if views > 0 else 0
            
            variants_data.append({
                'id': variant_id,
                'conversion_rate': conversion_rate,
                'views': views,
                'conversions': conversions,
            })

        if not variants_data:
            return None

        # 选择转化率最高的
        winner = max(variants_data, key=lambda x: x['conversion_rate'])

        # 检查统计显著性（简化版）
        # 实际应该使用卡方检验或Z检验
        confidence = self._calculate_confidence(variants_data)
        
        if confidence >= self.settings.get('confidence_level', 95):
            return winner['id']

        return None

    def _calculate_confidence(self, variants_data: List[Dict]) -> float:
        """
        计算置信度（简化实现）
        
        Args:
            variants_data: 变体数据
            
        Returns:
            置信度百分比
        """
        if len(variants_data) < 2:
            return 0

        # 简化的置信度计算
        # 实际应该使用统计学方法
        rates = [v['conversion_rate'] for v in variants_data]
        max_rate = max(rates)
        min_rate = min(rates)
        
        if max_rate == 0:
            return 0

        difference = max_rate - min_rate
        relative_difference = difference / max_rate

        # 基于相对差异估算置信度
        confidence = min(relative_difference * 1000, 99)

        return confidence

    def _validate_experiment(self, experiment_data: Dict[str, Any]) -> Dict[str, Any]:
        """验证实验数据"""
        if not experiment_data.get('name'):
            return {'valid': False, 'error': '实验名称不能为空'}

        variants = experiment_data.get('variants', [])
        if len(variants) < 2:
            return {'valid': False, 'error': '至少需要2个变体'}

        return {'valid': True, 'error': ''}

    def get_settings_ui(self) -> Dict[str, Any]:
        """返回设置界面配置"""
        return {
            'fields': [
                {
                    'key': 'enable_ab_testing',
                    'type': 'boolean',
                    'label': '启用A/B测试',
                },
                {
                    'key': 'default_traffic_split',
                    'type': 'number',
                    'label': '默认流量分配（%）',
                    'min': 10,
                    'max': 90,
                },
                {
                    'key': 'tracking_method',
                    'type': 'select',
                    'label': '追踪方式',
                    'options': [
                        {'value': 'cookie', 'label': 'Cookie'},
                        {'value': 'session', 'label': '会话'},
                        {'value': 'ip', 'label': 'IP地址'},
                    ],
                },
                {
                    'key': 'auto_select_winner',
                    'type': 'boolean',
                    'label': '自动选择优胜者',
                },
                {
                    'key': 'confidence_level',
                    'type': 'number',
                    'label': '置信度（%）',
                    'min': 90,
                    'max': 99,
                },
                {
                    'key': 'min_sample_size',
                    'type': 'number',
                    'label': '最小样本量',
                    'min': 50,
                    'max': 10000,
                },
            ],
            'actions': [
                {
                    'type': 'button',
                    'label': '查看所有实验',
                    'action': 'view_experiments',
                    'variant': 'outline',
                },
                {
                    'type': 'button',
                    'label': '新建实验',
                    'action': 'create_experiment',
                    'variant': 'primary',
                },
            ]
        }


# 插件实例
plugin_instance = ABTestingPlugin()
