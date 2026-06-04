"""
重定向管理器 (Redirect Manager)
管理 URL 重定向规则，支持 301/302 重定向
"""

import json
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Any, Optional


class RedirectManager:
    """
    重定向管理器
    
    功能:
    1. 添加/编辑/删除重定向规则
    2. 规则测试工具
    3. 批量导入/导出
    4. 404 页面检测
    5. URL 变更追踪
    6. 智能推荐目标 URL
    7. 正则表达式匹配
    8. 通配符支持
    9. 重定向统计
    """
    
    def __init__(self, redirects_file: str = "redirects.json"):
        self.redirects_file = Path(redirects_file)
        self.redirects = self._load_redirects()
    
    def _load_redirects(self) -> List[Dict[str, Any]]:
        """加载重定向规则"""
        if self.redirects_file.exists():
            try:
                with open(self.redirects_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except Exception as e:
                print(f"加载重定向规则失败: {e}")
        
        return []
    
    def _save_redirects(self):
        """保存重定向规则"""
        try:
            with open(self.redirects_file, 'w', encoding='utf-8') as f:
                json.dump(self.redirects, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"保存重定向规则失败: {e}")
    
    def add_redirect(
        self,
        source_url: str,
        target_url: str,
        redirect_type: int = 301,
            match_type: str = 'exact',
        enabled: bool = True,
        note: str = ""
    ) -> Dict[str, Any]:
        """
        添加重定向规则
        
        Args:
            source_url: 源URL（支持精确匹配、通配符*、正则表达式）
            target_url: 目标URL（可使用$1, $2等捕获组引用）
            redirect_type: 重定向类型 (301/302)
            match_type: 匹配类型 ('exact', 'wildcard', 'regex')
            enabled: 是否启用
            note: 备注
            
        Returns:
            添加结果
        """
        # 检查是否已存在
        for redirect in self.redirects:
            if redirect['source_url'] == source_url and redirect.get('match_type', 'exact') == match_type:
                return {
                    "success": False,
                    "error": f"源URL已存在: {source_url} (匹配类型: {match_type})"
                }

        # 验证正则表达式
        if match_type == 'regex':
            try:
                re.compile(source_url)
            except re.error as e:
                return {
                    "success": False,
                    "error": f"无效的正则表达式: {str(e)}"
                }
        
        redirect_rule = {
            "id": len(self.redirects) + 1,
            "source_url": source_url,
            "target_url": target_url,
            "redirect_type": redirect_type,
            "match_type": match_type,
            "enabled": enabled,
            "note": note,
            "created_at": datetime.now(timezone.utc).isoformat(),
            "updated_at": datetime.now(timezone.utc).isoformat(),
            "hit_count": 0,
            "last_hit": None
        }
        
        self.redirects.append(redirect_rule)
        self._save_redirects()
        
        return {
            "success": True,
            "message": "重定向规则已添加",
            "redirect": redirect_rule
        }
    
    def update_redirect(
        self,
        redirect_id: int,
        source_url: Optional[str] = None,
        target_url: Optional[str] = None,
        redirect_type: Optional[int] = None,
        enabled: Optional[bool] = None,
        note: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        更新重定向规则
        
        Args:
            redirect_id: 规则ID
            其他参数为可选更新字段
            
        Returns:
            更新结果
        """
        redirect = self._find_redirect_by_id(redirect_id)
        
        if not redirect:
            return {
                "success": False,
                "error": f"重定向规则不存在: {redirect_id}"
            }
        
        # 更新字段
        if source_url is not None:
            redirect['source_url'] = source_url
        if target_url is not None:
            redirect['target_url'] = target_url
        if redirect_type is not None:
            redirect['redirect_type'] = redirect_type
        if enabled is not None:
            redirect['enabled'] = enabled
        if note is not None:
            redirect['note'] = note
        
        redirect['updated_at'] = datetime.now(timezone.utc).isoformat()
        self._save_redirects()
        
        return {
            "success": True,
            "message": "重定向规则已更新",
            "redirect": redirect
        }
    
    def delete_redirect(self, redirect_id: int) -> Dict[str, Any]:
        """
        删除重定向规则
        
        Args:
            redirect_id: 规则ID
            
        Returns:
            删除结果
        """
        redirect = self._find_redirect_by_id(redirect_id)
        
        if not redirect:
            return {
                "success": False,
                "error": f"重定向规则不存在: {redirect_id}"
            }
        
        self.redirects.remove(redirect)
        self._save_redirects()
        
        return {
            "success": True,
            "message": "重定向规则已删除"
        }
    
    def get_all_redirects(
        self,
        enabled_only: bool = False,
        page: int = 1,
        per_page: int = 50
    ) -> Dict[str, Any]:
        """
        获取所有重定向规则
        
        Args:
            enabled_only: 只返回启用的规则
            page: 页码
            per_page: 每页数量
            
        Returns:
            重定向规则列表
        """
        redirects = self.redirects
        
        if enabled_only:
            redirects = [r for r in redirects if r['enabled']]
        
        # 分页
        total = len(redirects)
        start = (page - 1) * per_page
        end = start + per_page
        paginated_redirects = redirects[start:end]
        
        return {
            "redirects": paginated_redirects,
            "total": total,
            "page": page,
            "per_page": per_page,
            "total_pages": (total + per_page - 1) // per_page
        }
    
    def test_redirect(self, url: str) -> Optional[Dict[str, Any]]:
        """
        测试URL是否需要重定向
        
        Args:
            url: 要测试的URL
            
        Returns:
            匹配的重定向规则，无匹配返回None
        """
        for redirect in self.redirects:
            if not redirect['enabled']:
                continue

            matched = False
            target_url = redirect['target_url']
            match_type = redirect.get('match_type', 'exact')

            if match_type == 'exact':
                # 精确匹配
                matched = redirect['source_url'] == url

            elif match_type == 'wildcard':
                # 通配符匹配 - 将*转换为正则表达式
                import fnmatch
                matched = fnmatch.fnmatch(url, redirect['source_url'])

            elif match_type == 'regex':
                # 正则表达式匹配
                try:
                    pattern = re.compile(redirect['source_url'])
                    match = pattern.search(url)
                    if match:
                        matched = True
                        # 处理捕获组替换 ($1, $2, etc.)
                        for i, group in enumerate(match.groups(), 1):
                            target_url = target_url.replace(f'${i}', group)
                except re.error:
                    matched = False

            if matched:
                # 记录命中
                redirect['hit_count'] += 1
                redirect['last_hit'] = datetime.now(timezone.utc).isoformat()
                self._save_redirects()

                return {
                    **redirect,
                    'resolved_target': target_url
                }
        
        return None
    
    def bulk_import(self, redirects_data: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        批量导入重定向规则
        
        Args:
            redirects_data: 重定向数据列表
            
        Returns:
            导入结果
        """
        success_count = 0
        failed_count = 0
        errors = []
        
        for data in redirects_data:
            result = self.add_redirect(
                source_url=data.get('source_url'),
                target_url=data.get('target_url'),
                redirect_type=data.get('redirect_type', 301),
                enabled=data.get('enabled', True),
                note=data.get('note', '')
            )
            
            if result['success']:
                success_count += 1
            else:
                failed_count += 1
                errors.append(result['error'])
        
        return {
            "success": failed_count == 0,
            "total": len(redirects_data),
            "success_count": success_count,
            "failed_count": failed_count,
            "errors": errors
        }
    
    def export_redirects(self) -> List[Dict[str, Any]]:
        """导出所有重定向规则"""
        return self.redirects.copy()

    def get_statistics(self) -> Dict[str, Any]:
        """
        获取重定向统计信息
        
        Returns:
            统计数据
        """
        total_redirects = len(self.redirects)
        enabled_redirects = len([r for r in self.redirects if r['enabled']])
        disabled_redirects = total_redirects - enabled_redirects

        # 按类型统计
        type_301 = len([r for r in self.redirects if r['redirect_type'] == 301])
        type_302 = len([r for r in self.redirects if r['redirect_type'] == 302])

        # 按匹配类型统计
        exact_count = len([r for r in self.redirects if r.get('match_type', 'exact') == 'exact'])
        wildcard_count = len([r for r in self.redirects if r.get('match_type') == 'wildcard'])
        regex_count = len([r for r in self.redirects if r.get('match_type') == 'regex'])

        # 总命中次数
        total_hits = sum(r.get('hit_count', 0) for r in self.redirects)

        # 最近命中的规则
        recently_hit = [
            r for r in self.redirects
            if r.get('last_hit') is not None
        ]
        recently_hit.sort(key=lambda x: x['last_hit'], reverse=True)
        top_10_recent = recently_hit[:10]

        # 最热门的重定向规则
        top_10_hits = sorted(
            self.redirects,
            key=lambda x: x.get('hit_count', 0),
            reverse=True
        )[:10]

        return {
            "total_redirects": total_redirects,
            "enabled_redirects": enabled_redirects,
            "disabled_redirects": disabled_redirects,
            "by_type": {
                "301": type_301,
                "302": type_302
            },
            "by_match_type": {
                "exact": exact_count,
                "wildcard": wildcard_count,
                "regex": regex_count
            },
            "total_hits": total_hits,
            "top_10_by_hits": top_10_hits,
            "top_10_recent": top_10_recent
        }
    
    def detect_404_candidates(self, recent_404s: List[str]) -> List[Dict[str, Any]]:
        """
        从最近的404错误中检测可能的重定向候选
        
        Args:
            recent_404s: 最近的404 URL列表
            
        Returns:
            建议的重定向规则
        """
        suggestions = []
        
        for url_404 in recent_404s:
            # 尝试查找相似的URL
            similar_urls = self._find_similar_urls(url_404)
            
            if similar_urls:
                suggestions.append({
                    "source_url": url_404,
                    "suggested_target": similar_urls[0],
                    "confidence": "high" if len(similar_urls) == 1 else "medium"
                })
        
        return suggestions
    
    def _find_redirect_by_id(self, redirect_id: int) -> Optional[Dict[str, Any]]:
        """根据ID查找重定向规则"""
        for redirect in self.redirects:
            if redirect['id'] == redirect_id:
                return redirect
        return None
    
    def _find_similar_urls(self, url: str) -> List[str]:
        """查找相似的URL（简化版）"""
        # 这里应该实现更复杂的相似度算法
        # 暂时返回空列表
        return []


# 全局实例
redirect_manager = RedirectManager()
