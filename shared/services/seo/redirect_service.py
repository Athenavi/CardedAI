"""
URL重定向管理服务
提供URL重定向规则的创建、管理和统计功能
"""

from datetime import datetime
from typing import Dict, List, Any, Optional


class RedirectService:
    """
    URL重定向管理服务
    
    功能:
    1. 301永久重定向
    2. 302临时重定向
    3. 通配符匹配
    4. 正则表达式匹配
    5. 重定向统计
    6. 批量导入导出
    """

    def __init__(self):
        # 重定向类型
        self.redirect_types = {
            '301': {
                'name': '永久重定向',
                'description': 'SEO友好,告诉搜索引擎页面已永久移动',
                'cache': True
            },
            '302': {
                'name': '临时重定向',
                'description': '临时跳转,搜索引擎保留原URL',
                'cache': False
            }
        }

        # 匹配类型
        self.match_types = {
            'exact': {
                'name': '精确匹配',
                'description': '完全匹配URL路径'
            },
            'wildcard': {
                'name': '通配符匹配',
                'description': '使用*作为通配符'
            },
            'regex': {
                'name': '正则表达式',
                'description': '使用正则表达式匹配'
            }
        }

    def create_redirect(
            self,
            source_url: str,
            target_url: str,
            redirect_type: str = '301',
            match_type: str = 'exact',
            enabled: bool = True,
            note: str = ''
    ) -> Dict[str, Any]:
        """
        创建重定向规则
        
        Args:
            source_url: 源URL
            target_url: 目标URL
            redirect_type: 重定向类型(301/302)
            match_type: 匹配类型(exact/wildcard/regex)
            enabled: 是否启用
            note: 备注
            
        Returns:
            创建结果
        """
        try:
            # 验证URL格式
            if not source_url or not target_url:
                return {
                    'success': False,
                    'error': '源URL和目标URL不能为空'
                }

            # 验证重定向类型
            if redirect_type not in self.redirect_types:
                return {
                    'success': False,
                    'error': f'不支持的重定向类型: {redirect_type}'
                }

            # 验证匹配类型
            if match_type not in self.match_types:
                return {
                    'success': False,
                    'error': f'不支持的匹配类型: {match_type}'
                }

            # 如果是正则表达式,验证语法
            if match_type == 'regex':
                import re
                try:
                    re.compile(source_url)
                except re.error as e:
                    return {
                        'success': False,
                        'error': f'正则表达式语法错误: {str(e)}'
                    }

            redirect_data = {
                'source_url': source_url,
                'target_url': target_url,
                'redirect_type': redirect_type,
                'match_type': match_type,
                'enabled': enabled,
                'note': note,
                'created_at': datetime.now().isoformat(),
                'updated_at': datetime.now().isoformat(),
                'hit_count': 0,
                'last_hit': None
            }

            return {
                'success': True,
                'data': redirect_data
            }

        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }

    def match_redirect(
            self,
            request_url: str,
            redirects: List[Dict[str, Any]]
    ) -> Optional[Dict[str, Any]]:
        """
        匹配请求URL到重定向规则
        
        Args:
            request_url: 请求的URL
            redirects: 重定向规则列表
            
        Returns:
            匹配的重定向规则,无匹配返回None
        """
        for redirect in redirects:
            if not redirect.get('enabled'):
                continue

            source_url = redirect['source_url']
            match_type = redirect.get('match_type', 'exact')

            matched = False

            if match_type == 'exact':
                # 精确匹配
                matched = request_url == source_url

            elif match_type == 'wildcard':
                # 通配符匹配
                import fnmatch
                matched = fnmatch.fnmatch(request_url, source_url)

            elif match_type == 'regex':
                # 正则表达式匹配
                import re
                try:
                    pattern = re.compile(source_url)
                    matched = pattern.match(request_url) is not None
                except:
                    continue

            if matched:
                return redirect

        return None

    def validate_redirect_chain(
            self,
            source_url: str,
            redirects: List[Dict[str, Any]],
            max_depth: int = 10
    ) -> Dict[str, Any]:
        """
        检测重定向链(避免循环重定向)
        
        Args:
            source_url: 起始URL
            redirects: 重定向规则列表
            max_depth: 最大检测深度
            
        Returns:
            检测结果
        """
        chain = [source_url]
        current_url = source_url
        depth = 0

        while depth < max_depth:
            redirect = self.match_redirect(current_url, redirects)

            if not redirect:
                break

            next_url = redirect['target_url']

            # 检测循环
            if next_url in chain:
                return {
                    'valid': False,
                    'error': '检测到循环重定向',
                    'chain': chain + [next_url],
                    'is_cycle': True
                }

            chain.append(next_url)
            current_url = next_url
            depth += 1

        # 检查是否超过最大深度
        if depth >= max_depth:
            return {
                'valid': False,
                'error': f'重定向链过长(超过{max_depth}层)',
                'chain': chain,
                'is_too_long': True
            }

        return {
            'valid': True,
            'chain': chain,
            'final_url': current_url,
            'depth': depth
        }

    def get_redirect_statistics(
            self,
            redirects: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        获取重定向统计信息
        
        Args:
            redirects: 重定向规则列表
            
        Returns:
            统计数据
        """
        total_rules = len(redirects)
        enabled_rules = sum(1 for r in redirects if r.get('enabled'))
        disabled_rules = total_rules - enabled_rules

        total_hits = sum(r.get('hit_count', 0) for r in redirects)

        # 按类型统计
        type_stats = {}
        for redirect_type in self.redirect_types.keys():
            count = sum(1 for r in redirects if r.get('redirect_type') == redirect_type)
            type_stats[redirect_type] = count

        # 按匹配类型统计
        match_stats = {}
        for match_type in self.match_types.keys():
            count = sum(1 for r in redirects if r.get('match_type') == match_type)
            match_stats[match_type] = count

        # 最活跃的重定向
        most_active = sorted(
            [r for r in redirects if r.get('hit_count', 0) > 0],
            key=lambda x: x.get('hit_count', 0),
            reverse=True
        )[:10]

        return {
            'total_rules': total_rules,
            'enabled_rules': enabled_rules,
            'disabled_rules': disabled_rules,
            'total_hits': total_hits,
            'by_type': type_stats,
            'by_match_type': match_stats,
            'most_active': most_active
        }

    def export_redirects(
            self,
            redirects: List[Dict[str, Any]],
            format: str = 'json'
    ) -> str:
        """
        导出重定向规则
        
        Args:
            redirects: 重定向规则列表
            format: 导出格式(json/csv)
            
        Returns:
            导出的字符串
        """
        import json

        if format == 'json':
            return json.dumps(redirects, indent=2, ensure_ascii=False)

        elif format == 'csv':
            lines = ['Source URL,Target URL,Type,Match Type,Enabled,Note']
            for r in redirects:
                line = f'{r["source_url"]},{r["target_url"]},{r["redirect_type"]},{r.get("match_type", "exact")},{r.get("enabled", True)},"{r.get("note", "")}"'
                lines.append(line)
            return '\n'.join(lines)

        else:
            raise ValueError(f'不支持的导出格式: {format}')

    def import_redirects(
            self,
            data: str,
            format: str = 'json'
    ) -> Dict[str, Any]:
        """
        导入重定向规则
        
        Args:
            data: 导入的数据
            format: 数据格式(json/csv)
            
        Returns:
            导入结果
        """
        try:
            imported = []
            errors = []

            if format == 'json':
                import json
                redirects = json.loads(data)

                for i, redirect_data in enumerate(redirects):
                    result = self.create_redirect(**redirect_data)
                    if result['success']:
                        imported.append(result['data'])
                    else:
                        errors.append({'index': i, 'error': result['error']})

            elif format == 'csv':
                import csv
                import io

                csv_reader = csv.DictReader(io.StringIO(data))
                for i, row in enumerate(csv_reader):
                    try:
                        redirect_data = {
                            'source_url': row['Source URL'],
                            'target_url': row['Target URL'],
                            'redirect_type': row.get('Type', '301'),
                            'match_type': row.get('Match Type', 'exact'),
                            'enabled': row.get('Enabled', 'True').lower() == 'true',
                            'note': row.get('Note', '')
                        }
                        result = self.create_redirect(**redirect_data)
                        if result['success']:
                            imported.append(result['data'])
                        else:
                            errors.append({'index': i, 'error': result['error']})
                    except Exception as e:
                        errors.append({'index': i, 'error': str(e)})

            return {
                'success': True,
                'imported': len(imported),
                'errors': len(errors),
                'details': imported,
                'error_details': errors
            }

        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }

    def generate_htaccess_rules(
            self,
            redirects: List[Dict[str, Any]]
    ) -> str:
        """
        生成Apache .htaccess重定向规则
        
        Args:
            redirects: 重定向规则列表
            
        Returns:
            .htaccess规则字符串
        """
        lines = ['# Generated by Fast Blog Redirect Manager', '']

        for redirect in redirects:
            if not redirect.get('enabled'):
                continue

            source = redirect['source_url']
            target = redirect['target_url']
            redirect_type = redirect.get('redirect_type', '301')
            match_type = redirect.get('match_type', 'exact')

            if match_type == 'exact':
                lines.append(f'Redirect {redirect_type} {source} {target}')
            elif match_type == 'regex':
                # Apache mod_rewrite规则
                lines.append(f'RewriteEngine On')
                lines.append(f'RewriteRule ^{source}$ {target} [R={redirect_type},L]')

            lines.append('')

        return '\n'.join(lines)

    def generate_nginx_rules(
            self,
            redirects: List[Dict[str, Any]]
    ) -> str:
        """
        生成Nginx重定向规则
        
        Args:
            redirects: 重定向规则列表
            
        Returns:
            Nginx配置字符串
        """
        lines = ['# Generated by Fast Blog Redirect Manager', '']

        for redirect in redirects:
            if not redirect.get('enabled'):
                continue

            source = redirect['source_url']
            target = redirect['target_url']
            redirect_type = redirect.get('redirect_type', '301')

            lines.append(f'rewrite ^{source}$ {target} permanent;' if redirect_type == '301'
                         else f'rewrite ^{source}$ {target} redirect;')

        return '\n'.join(lines)


# 全局实例
redirect_service = RedirectService()
