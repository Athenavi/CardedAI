#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
更新历史记录模块 - 简化版
记录每次更新的详细信息
"""

import json

from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional

from src.unified_logger import default_logger as logger


class UpdateHistoryManager:
    """更新历史管理器（简化版）"""
    
    def __init__(self, history_file: str = "logs/update_history.json"):
        self.history_file = Path(history_file)
        self.history_data = {'updates': [], 'last_update': None}
        self._load_history()
    
    def _load_history(self):
        """加载历史记录"""
        if self.history_file.exists():
            try:
                with open(self.history_file, 'r', encoding='utf-8') as f:
                    self.history_data = json.load(f)
            except Exception as e:
                logger.error(f"加载历史记录失败：{e}")
                self.history_data = {'updates': [], 'last_update': None}
        self._save_history()
    
    def _save_history(self):
        """保存历史记录"""
        try:
            self.history_file.parent.mkdir(parents=True, exist_ok=True)
            with open(self.history_file, 'w', encoding='utf-8') as f:
                json.dump(self.history_data, f, indent=2, ensure_ascii=False)
        except Exception as e:
            logger.error(f"保存历史记录失败：{e}")
    
    def add(self, from_version: str, to_version: str, status: str, **kwargs):
        """添加更新记录
        
        Args:
            from_version: 起始版本
            to_version: 目标版本
            status: 状态 (success/failed/rollback)
            **kwargs: 其他参数 (backup_path, duration, error 等)
        """
        record = {
            'from_version': from_version,
            'to_version': to_version,
            'status': status,
            'timestamp': datetime.now().isoformat(),
            **kwargs
        }
        
        self.history_data['updates'].append(record)
        self.history_data['last_update'] = record['timestamp']
        self.history_data['updates'].sort(key=lambda x: x.get('timestamp', ''), reverse=True)
        self._save_history()
        
        logger.info(f"已记录更新：{from_version} -> {to_version} ({status})")
    
    def get_recent(self, limit: int = 10) -> List[Dict]:
        """获取最近的更新记录"""
        return self.history_data.get('updates', [])[:limit]
    
    def get_last(self) -> Optional[Dict]:
        """获取最后一次更新记录"""
        updates = self.history_data.get('updates', [])
        return updates[0] if updates else None


# 全局单例
update_history_manager = UpdateHistoryManager()


def add_update_history(from_version: str, to_version: str, status: str, **kwargs):
    """便捷函数：添加更新历史"""
    update_history_manager.add(from_version, to_version, status, **kwargs)
