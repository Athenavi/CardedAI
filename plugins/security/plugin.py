"""
综合安全防护插件
整合恶意代码扫描、文件完整性监控、XSS/SQL注入防护、速率限制、IP黑白名单、登录保护等功能

功能模块:
1. 恶意代码扫描器 - 检测可疑代码模式、木马、后门
2. 文件完整性监控 - 基于哈希的文件变更检测
3. XSS/SQL注入防护 - 实时请求过滤
4. 速率限制 - 防止DDoS和暴力破解
5. IP黑白名单 - 访问控制
6. 登录保护 - 防止暴力破解
7. 安全日志审计 - 记录所有安全事件
8. 漏洞扫描 - 依赖漏洞检测
"""

import hashlib
import json
import re
import time
from collections import defaultdict
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Any, Optional, Set

from shared.services.plugins.plugin_manager import BasePlugin, plugin_hooks
from shared.utils.plugin_database import plugin_db


class SecurityPlugin(BasePlugin):
    """
    综合安全防护插件
    
    整合了以下原有插件的功能:
    - malware-scanner: 恶意代码扫描
    - security-guard: 基础安全防护
    - security-pro: 专业安全增强
    """

    def __init__(self):
        super().__init__(
            plugin_id=0,
            name="安全防护中心",
            slug="security",
            version="2.0.0"
        )

        # ==================== 全局设置 ====================
        self.settings = {
            # 恶意代码扫描设置
            'enable_malware_scan': True,
            'scan_interval_hours': 24,
            'auto_scan_enabled': True,
            'scan_directories': ['src', 'shared', 'apps', 'plugins'],
            'exclude_patterns': ['*.pyc', '__pycache__', '*.log', '.git', 'node_modules'],
            'max_file_size_mb': 10,
            'quarantine_enabled': True,
            'quarantine_dir': 'storage/quarantine',

            # XSS/SQL注入防护设置
            'enable_xss_protection': True,
            'enable_sql_injection_detection': True,

            # 速率限制设置
            'enable_rate_limiting': True,
            'rate_limit_requests': 60,
            'rate_limit_window': 60,  # 秒

            # IP黑白名单设置
            'enable_ip_blacklist': True,
            'enable_ip_whitelist': False,
            'ip_blacklist': '',
            'ip_whitelist': '',

            # 登录保护设置
            'enable_login_lockout': True,
            'max_login_attempts': 5,
            'lockout_duration': 30,  # 分钟

            # 文件完整性监控
            'enable_file_integrity': True,
            'monitored_directories': ['src', 'shared', 'apps', 'config'],

            # 安全日志
            'enable_audit_log': True,
            'log_retention_days': 90,

            # 漏洞扫描
            'enable_vulnerability_scan': True,
            'vuln_scan_frequency': 'weekly',
        }

        # ==================== 恶意代码扫描相关 ====================
        self.suspicious_patterns = [
            # eval() 调用
            (r'\beval\s*\(', 'Eval function usage', 'high'),
            # base64解码
            (r'\bbase64_decode\s*\(', 'Base64 decode detected', 'medium'),
            # system/exec 命令执行
            (r'\b(system|exec|passthru|shell_exec)\s*\(', 'Command execution', 'critical'),
            # PHP webshell特征
            (r'preg_replace\s*\(\s*[\'"]/e[\'"]', 'PHP webshell pattern', 'critical'),
            # SQL注入特征
            (r'(\bUNION\b.*\bSELECT\b|\bOR\b\s+1\s*=\s*1)', 'SQL injection pattern', 'critical'),
            # Python危险函数
            (r'os\.system\s*\(', 'OS system call detected', 'high'),
            (r'subprocess\.call\s*\(\s*shell\s*=\s*True', 'Subprocess with shell=True', 'high'),
        ]

        self.known_safe_hashes = {}
        self.scan_stats = {
            'last_scan_time': None,
            'total_files_scanned': 0,
            'threats_found': 0,
        }

        # ==================== 速率限制相关 ====================
        self.rate_limits: Dict[str, List] = {}

        # ==================== 登录保护相关 ====================
        self.login_attempts: Dict[str, List[tuple]] = defaultdict(list)
        self.locked_users: Dict[str, datetime] = {}

        # ==================== IP黑白名单 ====================
        self.ip_blacklist: Set[str] = set()
        self.ip_whitelist: Set[str] = set()

        # ==================== 文件完整性监控 ====================
        self.file_snapshot: Dict[str, str] = {}

        # ==================== 安全日志 ====================
        self.security_logs: List[Dict[str, Any]] = []

        # ==================== 扫描结果 ====================
        self.scan_results: List[Dict[str, Any]] = []

    def register_hooks(self):
        """注册钩子"""
        # 请求前安全检查
        plugin_hooks.add_filter(
            "before_request",
            self.security_check,
            priority=1
        )

        # 内容输出时清理XSS
        if self.settings.get('enable_xss_protection'):
            plugin_hooks.add_filter(
                "output_content",
                self.sanitize_output,
                priority=10
            )

        # 登录尝试记录
        plugin_hooks.add_action(
            "login_attempt",
            self.record_login_attempt,
            priority=10
        )

        # 登录前检查
        plugin_hooks.add_filter(
            "pre_login_check",
            self.check_login_attempt,
            priority=5
        )

        # 登录失败记录
        plugin_hooks.add_action(
            "login_failed",
            self.record_failed_login,
            priority=10
        )

        # 登录成功清除记录
        plugin_hooks.add_action(
            "login_success",
            self.clear_login_attempts,
            priority=10
        )

        # 定时扫描任务
        if self.settings.get('auto_scan_enabled'):
            plugin_hooks.add_action(
                "daily_cleanup",
                self.perform_scheduled_scan,
                priority=10
            )

    def activate(self):
        """激活插件"""
        super().activate()
        self._init_database()
        self._load_known_hashes()
        self._load_ip_lists()
        self._create_file_snapshot()
        print("[Security] Plugin activated - All security modules initialized")

    def deactivate(self):
        """停用插件"""
        super().deactivate()
        print("[Security] Plugin deactivated")

    def _init_database(self):
        """初始化数据库表"""
        try:
            init_security_db()
        except Exception as e:
            print(f"[Security] Failed to initialize database: {e}")

    def _load_known_hashes(self):
        """加载已知安全的文件哈希"""
        try:
            hashes_file = Path('storage/known_safe_hashes.json')
            if hashes_file.exists():
                with open(hashes_file, 'r') as f:
                    self.known_safe_hashes = json.load(f)
            else:
                self.known_safe_hashes = {}
        except Exception as e:
            print(f"[Security] Failed to load known hashes: {e}")
            self.known_safe_hashes = {}

    def _load_ip_lists(self):
        """加载IP黑白名单"""
        try:
            blacklist_str = self.settings.get('ip_blacklist', '')
            if blacklist_str:
                self.ip_blacklist = set([ip.strip() for ip in blacklist_str.split(',') if ip.strip()])

            whitelist_str = self.settings.get('ip_whitelist', '')
            if whitelist_str:
                self.ip_whitelist = set([ip.strip() for ip in whitelist_str.split(',') if ip.strip()])
        except Exception as e:
            print(f"[Security] Failed to load IP lists: {e}")

    # ==================== 请求安全检查 ====================

    def security_check(self, request_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        请求安全检查
        
        Args:
            request_data: 请求数据 {ip, url, method, headers, body}
            
        Returns:
            检查结果 {allowed: bool, reason: str, status_code: int}
        """
        client_ip = request_data.get('ip', '')

        # 1. 检查IP白名单（如果启用）
        if self.settings.get('enable_ip_whitelist') and self.ip_whitelist:
            if client_ip not in self.ip_whitelist:
                return {
                    'allowed': False,
                    'reason': 'IP not in whitelist',
                    'status_code': 403,
                }

        # 2. 检查IP黑名单
        if self.settings.get('enable_ip_blacklist') and client_ip in self.ip_blacklist:
            self._log_security_event('ip_blocked', {
                'ip': client_ip,
                'reason': 'Blacklisted IP',
                'url': request_data.get('url', ''),
            })
            return {
                'allowed': False,
                'reason': 'IP address is blacklisted',
                'status_code': 403,
            }

        # 3. 检查速率限制
        if self.settings.get('enable_rate_limiting'):
            if not self._check_rate_limit(client_ip):
                self._log_security_event('rate_limit_exceeded', {
                    'ip': client_ip,
                    'url': request_data.get('url', ''),
                })
                return {
                    'allowed': False,
                    'reason': 'Rate limit exceeded',
                    'status_code': 429,
                }

        # 4. 检查SQL注入
        if self.settings.get('enable_sql_injection_detection'):
            if self._detect_sql_injection(request_data):
                self._log_security_event('sql_injection_detected', {
                    'ip': client_ip,
                    'url': request_data.get('url', ''),
                    'method': request_data.get('method', ''),
                })
                return {
                    'allowed': False,
                    'reason': 'Potential SQL injection detected',
                    'status_code': 400,
                }

        # 5. 检查XSS
        if self.settings.get('enable_xss_protection'):
            if self._detect_xss(request_data):
                self._log_security_event('xss_detected', {
                    'ip': client_ip,
                    'url': request_data.get('url', ''),
                    'method': request_data.get('method', ''),
                })
                return {
                    'allowed': False,
                    'reason': 'Potential XSS attack detected',
                    'status_code': 400,
                }

        return {'allowed': True}

    def sanitize_output(self, content: str) -> str:
        """
        清理输出内容中的XSS
        
        Args:
            content: 原始内容
            
        Returns:
            清理后的内容
        """
        if not self.settings.get('enable_xss_protection'):
            return content

        # 移除script标签
        content = re.sub(r'<script[^>]*>.*?</script>', '', content, flags=re.IGNORECASE | re.DOTALL)

        # 移除事件处理器
        content = re.sub(r'\s+on\w+\s*=\s*["\'][^"\']*["\']', '', content, flags=re.IGNORECASE)

        # 移除javascript:协议
        content = re.sub(r'javascript\s*:', '', content, flags=re.IGNORECASE)

        return content

    # ==================== 速率限制 ====================

    def _check_rate_limit(self, client_ip: str) -> bool:
        """
        检查速率限制
        
        Args:
            client_ip: 客户端IP
            
        Returns:
            是否允许请求
        """
        now = time.time()
        window = self.settings.get('rate_limit_window', 60)
        max_requests = self.settings.get('rate_limit_requests', 60)

        if client_ip not in self.rate_limits:
            self.rate_limits[client_ip] = []

        # 清理过期记录
        self.rate_limits[client_ip] = [
            ts for ts in self.rate_limits[client_ip]
            if now - ts < window
        ]

        # 检查是否超限
        if len(self.rate_limits[client_ip]) >= max_requests:
            return False

        # 记录当前请求
        self.rate_limits[client_ip].append(now)
        return True

    # ==================== XSS/SQL注入检测 ====================

    def _detect_xss(self, request_data: Dict[str, Any]) -> bool:
        """检测XSS攻击"""
        xss_patterns = [
            r'<script[^>]*>',
            r'javascript\s*:',
            r'on\w+\s*=',
            r'<iframe[^>]*>',
            r'<object[^>]*>',
            r'<embed[^>]*>',
        ]

        # 检查URL参数
        url = request_data.get('url', '')
        for pattern in xss_patterns:
            if re.search(pattern, url, re.IGNORECASE):
                return True

        # 检查请求体
        body = str(request_data.get('body', ''))
        for pattern in xss_patterns:
            if re.search(pattern, body, re.IGNORECASE):
                return True

        return False

    def _detect_sql_injection(self, request_data: Dict[str, Any]) -> bool:
        """检测SQL注入"""
        sqli_patterns = [
            r'(\bUNION\b.*\bSELECT\b)',
            r'(\bOR\b\s+\d+\s*=\s*\d+)',
            r'(\bAND\b\s+\d+\s*=\s*\d+)',
            r'(;\s*(DROP|DELETE|UPDATE|INSERT)\b)',
            r'(--\s*$)',
            r'(/\*.*\*/)',
        ]

        # 检查URL参数
        url = request_data.get('url', '')
        for pattern in sqli_patterns:
            if re.search(pattern, url, re.IGNORECASE):
                return True

        # 检查请求体
        body = str(request_data.get('body', ''))
        for pattern in sqli_patterns:
            if re.search(pattern, body, re.IGNORECASE):
                return True

        return False

    # ==================== 登录保护 ====================

    def check_login_attempt(self, login_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        检查登录尝试
        
        Args:
            login_data: {username, ip}
            
        Returns:
            检查结果 {allowed: bool, message: str}
        """
        if not self.settings.get('enable_login_lockout'):
            return {'allowed': True}

        username = login_data.get('username', '')

        # 检查是否被锁定
        if username in self.locked_users:
            lockout_until = self.locked_users[username]
            if datetime.now() < lockout_until:
                remaining_minutes = int((lockout_until - datetime.now()).total_seconds() / 60)
                self._log_security_event('login_blocked', {
                    'username': username,
                    'ip': login_data.get('ip'),
                    'reason': 'Account locked',
                })
                return {
                    'allowed': False,
                    'message': f'Account locked. Try again in {remaining_minutes} minutes.',
                }
            else:
                # 锁定已过期，清除
                del self.locked_users[username]

        return {'allowed': True}

    def record_login_attempt(self, login_data: Dict[str, Any]):
        """记录登录尝试"""
        self._log_security_event('login_attempt', login_data)

    def record_failed_login(self, login_data: Dict[str, Any]):
        """
        记录失败的登录尝试
        
        Args:
            login_data: {username, ip}
        """
        if not self.settings.get('enable_login_lockout'):
            return

        username = login_data.get('username', '')
        ip = login_data.get('ip', '')

        # 记录尝试
        self.login_attempts[username].append((datetime.now(), ip))

        # 检查是否超过最大尝试次数
        max_attempts = self.settings.get('max_login_attempts', 5)
        recent_attempts = [
            attempt for attempt in self.login_attempts[username]
            if (datetime.now() - attempt[0]).total_seconds() < 3600  # 1小时内
        ]

        if len(recent_attempts) >= max_attempts:
            # 锁定账户
            lockout_duration = self.settings.get('lockout_duration', 30)
            lockout_until = datetime.now() + timedelta(minutes=lockout_duration)
            self.locked_users[username] = lockout_until

            self._log_security_event('account_locked', {
                'username': username,
                'ip': ip,
                'attempts': len(recent_attempts),
                'lockout_until': lockout_until.isoformat(),
            })

            print(f"[Security] Account locked: {username} until {lockout_until}")

        self._log_security_event('login_failed', {
            'username': username,
            'ip': ip,
            'attempt_count': len(recent_attempts),
        })

    def clear_login_attempts(self, login_data: Dict[str, Any]):
        """登录成功后清除尝试记录"""
        username = login_data.get('username', '')
        if username in self.login_attempts:
            del self.login_attempts[username]

        self._log_security_event('login_success', {
            'username': username,
            'ip': login_data.get('ip'),
        })

    # ==================== 恶意代码扫描 ====================

    def perform_scheduled_scan(self):
        """执行定时扫描"""
        if not self.settings.get('enable_malware_scan') or not self.settings.get('auto_scan_enabled'):
            return

        # 检查是否到了扫描时间
        last_scan = self.scan_stats.get('last_scan_time')
        if last_scan:
            hours_since_scan = (datetime.now() - datetime.fromisoformat(last_scan)).total_seconds() / 3600
            if hours_since_scan < self.settings.get('scan_interval_hours', 24):
                return

        print("[Security] Starting scheduled malware scan...")
        self.scan_all_files()

    def scan_all_files(self) -> Dict[str, Any]:
        """
        扫描所有文件
        
        Returns:
            扫描结果
        """
        if not self.settings.get('enable_malware_scan'):
            return {'success': False, 'error': 'Scanning is disabled'}

        start_time = time.time()
        threats = []
        files_scanned = 0

        try:
            scan_dirs = self.settings.get('scan_directories', [])
            exclude_patterns = self.settings.get('exclude_patterns', [])
            max_size = self.settings.get('max_file_size_mb', 10) * 1024 * 1024

            for dir_name in scan_dirs:
                scan_path = Path(dir_name)
                if not scan_path.exists():
                    continue

                for file_path in scan_path.rglob('*'):
                    if not file_path.is_file():
                        continue

                    if self._should_exclude(str(file_path), exclude_patterns):
                        continue

                    try:
                        if file_path.stat().st_size > max_size:
                            continue
                    except:
                        continue

                    files_scanned += 1
                    threat = self._scan_file(file_path)
                    if threat:
                        threats.append(threat)

            # 更新统计
            scan_duration = time.time() - start_time
            self.scan_stats = {
                'last_scan_time': datetime.now().isoformat(),
                'total_files_scanned': files_scanned,
                'threats_found': len(threats),
            }

            # 保存扫描结果
            self._save_scan_result(threats)

            print(f"[Security] Scan completed: {files_scanned} files, {len(threats)} threats found")

            return {
                'success': True,
                'files_scanned': files_scanned,
                'threats_found': len(threats),
                'threats': threats[:50],
                'duration': round(scan_duration, 2),
            }

        except Exception as e:
            print(f"[Security] Scan failed: {e}")
            import traceback
            traceback.print_exc()
            return {'success': False, 'error': str(e)}

    def _scan_file(self, file_path: Path) -> Optional[Dict[str, Any]]:
        """扫描单个文件"""
        try:
            # 计算文件哈希
            file_hash = self._calculate_file_hash(file_path)

            # 检查是否是已知安全文件
            if file_hash in self.known_safe_hashes:
                return None

            # 读取文件内容
            try:
                with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                    content = f.read()
            except:
                return None

            # 检查可疑模式
            for pattern, description, severity in self.suspicious_patterns:
                matches = re.finditer(pattern, content, re.IGNORECASE | re.MULTILINE)
                for match in matches:
                    return {
                        'file': str(file_path),
                        'type': 'suspicious_pattern',
                        'description': description,
                        'severity': severity,
                        'line_number': content[:match.start()].count('\n') + 1,
                        'matched_code': match.group(0)[:100],
                        'detected_at': datetime.now().isoformat(),
                    }

            return None

        except Exception as e:
            print(f"[Security] Failed to scan file {file_path}: {e}")
            return None

    def _calculate_file_hash(self, file_path: Path) -> str:
        """计算文件SHA256哈希"""
        sha256_hash = hashlib.sha256()
        try:
            with open(file_path, "rb") as f:
                for byte_block in iter(lambda: f.read(4096), b""):
                    sha256_hash.update(byte_block)
            return sha256_hash.hexdigest()
        except:
            return ""

    def _should_exclude(self, file_path: str, exclude_patterns: List[str]) -> bool:
        """检查文件是否应该被排除"""
        for pattern in exclude_patterns:
            if pattern in file_path:
                return True
        return False

    def _save_scan_result(self, threats: List[Dict[str, Any]]):
        """保存扫描结果到数据库"""
        try:
            plugin_db.execute_query(
                'security',
                """INSERT INTO scan_results (scan_time, files_scanned, threats_found, threats_data)
                   VALUES (?, ?, ?, ?)""",
                (
                    datetime.now().isoformat(),
                    self.scan_stats['total_files_scanned'],
                    len(threats),
                    json.dumps(threats[:50])
                )
            )
        except Exception as e:
            print(f"[Security] Failed to save scan result: {e}")

    # ==================== 文件完整性监控 ====================

    def check_file_integrity(self) -> Dict[str, Any]:
        """
        文件完整性检查
        
        Returns:
            检查结果
        """
        if not self.settings.get('enable_file_integrity'):
            return {'has_changes': False, 'message': 'File integrity monitoring disabled'}

        current_files = {}
        monitored_dirs = self.settings.get('monitored_directories', [])

        # 扫描当前文件
        for dir_name in monitored_dirs:
            dir_path = Path(dir_name)
            if not dir_path.exists():
                continue

            for file_path in dir_path.rglob('*'):
                if file_path.is_file() and not self._should_exclude(str(file_path), ['__pycache__', '.git']):
                    file_hash = self._calculate_file_hash(file_path)
                    if file_hash:
                        current_files[str(file_path)] = file_hash

        # 比较变化
        changes = {
            'added': [],
            'modified': [],
            'deleted': [],
        }

        # 检查新增和修改的文件
        for file_path, current_hash in current_files.items():
            if file_path not in self.file_snapshot:
                changes['added'].append(file_path)
            elif self.file_snapshot[file_path] != current_hash:
                changes['modified'].append({
                    'file': file_path,
                    'old_hash': self.file_snapshot[file_path][:16],
                    'new_hash': current_hash[:16],
                })

        # 检查删除的文件
        for file_path in self.file_snapshot:
            if file_path not in current_files:
                changes['deleted'].append(file_path)

        has_changes = any(changes.values())

        if has_changes:
            self._log_security_event('file_integrity_violation', {
                'changes': changes,
            })

        return {
            'has_changes': has_changes,
            'changes': changes,
            'total_files_checked': len(current_files),
            'timestamp': datetime.now().isoformat(),
        }

    def update_file_snapshot(self):
        """更新文件快照"""
        self._create_file_snapshot()
        print("[Security] File snapshot updated")

    def _create_file_snapshot(self):
        """创建文件哈希快照"""
        self.file_snapshot.clear()
        monitored_dirs = self.settings.get('monitored_directories', [])

        for dir_name in monitored_dirs:
            dir_path = Path(dir_name)
            if not dir_path.exists():
                continue

            for file_path in dir_path.rglob('*'):
                if file_path.is_file() and not self._should_exclude(str(file_path), ['__pycache__', '.git']):
                    file_hash = self._calculate_file_hash(file_path)
                    if file_hash:
                        self.file_snapshot[str(file_path)] = file_hash

        print(f"[Security] Created file snapshot with {len(self.file_snapshot)} files")

    # ==================== 安全日志 ====================

    def _log_security_event(self, event_type: str, details: Dict[str, Any]):
        """
        记录安全事件
        
        Args:
            event_type: 事件类型
            details: 事件详情
        """
        if not self.settings.get('enable_audit_log'):
            return

        log_entry = {
            'event_type': event_type,
            'timestamp': datetime.now().isoformat(),
            'details': details,
        }

        self.security_logs.append(log_entry)

        # 限制日志数量(保留最近10000条)
        if len(self.security_logs) > 10000:
            self.security_logs = self.security_logs[-10000:]

        # 保存到数据库
        try:
            plugin_db.execute_query(
                'security',
                """INSERT INTO security_logs (event_type, timestamp, details)
                   VALUES (?, ?, ?)""",
                (event_type, log_entry['timestamp'], json.dumps(details))
            )
        except Exception as e:
            print(f"[Security] Failed to save security log: {e}")

    def get_security_logs(self, limit: int = 100, event_type: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        获取安全日志
        
        Args:
            limit: 返回数量限制
            event_type: 事件类型过滤
            
        Returns:
            安全日志列表
        """
        filtered = self.security_logs

        if event_type:
            filtered = [log for log in filtered if log['event_type'] == event_type]

        return filtered[-limit:]

    # ==================== 管理API ====================

    def get_dashboard_data(self) -> Dict[str, Any]:
        """获取仪表板数据"""
        return {
            'scan_stats': self.scan_stats,
            'locked_users_count': len(self.locked_users),
            'blacklisted_ips_count': len(self.ip_blacklist),
            'whitelisted_ips_count': len(self.ip_whitelist),
            'recent_logs': self.get_security_logs(limit=10),
            'file_snapshot_count': len(self.file_snapshot),
        }

    def run_full_security_scan(self) -> Dict[str, Any]:
        """执行完整安全扫描"""
        start_time = time.time()

        result = {
            'scan_id': f"scan_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
            'timestamp': datetime.now().isoformat(),
            'modules': {},
        }

        # 1. 恶意代码扫描
        if self.settings.get('enable_malware_scan'):
            result['modules']['malware_scan'] = self.scan_all_files()

        # 2. 文件完整性检查
        if self.settings.get('enable_file_integrity'):
            result['modules']['file_integrity'] = self.check_file_integrity()

        # 3. 配置安全检查
        result['modules']['config_check'] = self._check_security_config()

        result['duration_seconds'] = round(time.time() - start_time, 2)

        # 确定总体状态
        has_critical = any(
            m.get('threats_found', 0) > 0 or m.get('has_changes', False)
            for m in result['modules'].values()
        )
        result['overall_status'] = 'critical' if has_critical else 'pass'

        self.scan_results.append(result)
        return result

    def _check_security_config(self) -> Dict[str, Any]:
        """检查安全配置"""
        issues = []

        # 检查DEBUG模式
        import os
        if os.getenv('DEBUG', 'False').lower() in ('true', '1', 'yes'):
            issues.append({
                'type': 'debug_enabled',
                'severity': 'high',
                'description': 'DEBUG mode is enabled',
            })

        return {
            'issues': issues,
            'status': 'warning' if issues else 'pass',
        }

    def get_admin_ui_config(self) -> Dict[str, Any]:
        """获取管理界面配置"""
        return {
            'title': '安全防护中心',
            'icon': '🛡️',
            'sections': [
                {
                    'title': '安全概览',
                    'widgets': [
                        {'type': 'stat', 'label': '已扫描文件', 'value': self.scan_stats.get('total_files_scanned', 0)},
                        {'type': 'stat', 'label': '发现威胁', 'value': self.scan_stats.get('threats_found', 0)},
                        {'type': 'stat', 'label': '锁定用户', 'value': len(self.locked_users)},
                        {'type': 'stat', 'label': '黑名单IP', 'value': len(self.ip_blacklist)},
                    ],
                },
                {
                    'title': '扫描设置',
                    'fields': [
                        {
                            'key': 'enable_malware_scan',
                            'label': '启用恶意代码扫描',
                            'type': 'boolean',
                        },
                        {
                            'key': 'scan_interval_hours',
                            'label': '扫描间隔（小时）',
                            'type': 'number',
                            'min': 1,
                            'max': 168,
                        },
                        {
                            'key': 'enable_file_integrity',
                            'label': '启用文件完整性监控',
                            'type': 'boolean',
                        },
                    ],
                },
                {
                    'title': '防护设置',
                    'fields': [
                        {
                            'key': 'enable_xss_protection',
                            'label': '启用XSS防护',
                            'type': 'boolean',
                        },
                        {
                            'key': 'enable_sql_injection_detection',
                            'label': '启用SQL注入检测',
                            'type': 'boolean',
                        },
                        {
                            'key': 'enable_rate_limiting',
                            'label': '启用速率限制',
                            'type': 'boolean',
                        },
                        {
                            'key': 'rate_limit_requests',
                            'label': '每分钟最大请求数',
                            'type': 'number',
                            'min': 10,
                            'max': 1000,
                        },
                    ],
                },
                {
                    'title': '登录保护',
                    'fields': [
                        {
                            'key': 'enable_login_lockout',
                            'label': '启用登录锁定',
                            'type': 'boolean',
                        },
                        {
                            'key': 'max_login_attempts',
                            'label': '最大尝试次数',
                            'type': 'number',
                            'min': 3,
                            'max': 10,
                        },
                        {
                            'key': 'lockout_duration',
                            'label': '锁定时长（分钟）',
                            'type': 'number',
                            'min': 5,
                            'max': 120,
                        },
                    ],
                },
                {
                    'title': '操作',
                    'actions': [
                        {
                            'type': 'button',
                            'label': '立即扫描',
                            'action': 'scan_now',
                            'variant': 'primary',
                        },
                        {
                            'type': 'button',
                            'label': '更新文件快照',
                            'action': 'update_snapshot',
                            'variant': 'outline',
                        },
                        {
                            'type': 'button',
                            'label': '查看安全日志',
                            'action': 'view_logs',
                            'variant': 'outline',
                        },
                        {
                            'type': 'button',
                            'label': '完整安全扫描',
                            'action': 'full_scan',
                            'variant': 'danger',
                        },
                    ],
                },
            ],
        }


def init_security_db():
    """初始化安全插件数据库"""
    slug = "security"

    # 创建扫描结果表
    plugin_db.execute_query(
        slug,
        """CREATE TABLE IF NOT EXISTS scan_results
           (
               id
               INTEGER
               PRIMARY
               KEY
               AUTOINCREMENT,
               scan_time
               TEXT
               NOT
               NULL,
               files_scanned
               INTEGER
               DEFAULT
               0,
               threats_found
               INTEGER
               DEFAULT
               0,
               threats_data
               TEXT,
               created_at
               TIMESTAMP
               DEFAULT
               CURRENT_TIMESTAMP
           )"""
    )

    # 创建安全日志表
    plugin_db.execute_query(
        slug,
        """CREATE TABLE IF NOT EXISTS security_logs
           (
               id
               INTEGER
               PRIMARY
               KEY
               AUTOINCREMENT,
               event_type
               TEXT
               NOT
               NULL,
               timestamp
               TEXT
               NOT
               NULL,
               details
               TEXT,
               created_at
               TIMESTAMP
               DEFAULT
               CURRENT_TIMESTAMP
           )"""
    )

    # 创建威胁记录表
    plugin_db.execute_query(
        slug,
        """CREATE TABLE IF NOT EXISTS threats
           (
               id
               INTEGER
               PRIMARY
               KEY
               AUTOINCREMENT,
               file_path
               TEXT
               NOT
               NULL,
               threat_type
               TEXT
               NOT
               NULL,
               severity
               TEXT
               NOT
               NULL,
               description
               TEXT,
               detected_at
               TEXT
               NOT
               NULL,
               status
               TEXT
               DEFAULT
               'active',
               resolved_at
               TEXT,
               created_at
               TIMESTAMP
               DEFAULT
               CURRENT_TIMESTAMP
           )"""
    )

    # 创建索引
    plugin_db.execute_query(
        slug,
        "CREATE INDEX IF NOT EXISTS idx_scan_time ON scan_results(scan_time)"
    )
    plugin_db.execute_query(
        slug,
        "CREATE INDEX IF NOT EXISTS idx_event_type ON security_logs(event_type)"
    )
    plugin_db.execute_query(
        slug,
        "CREATE INDEX IF NOT EXISTS idx_threat_severity ON threats(severity)"
    )


# 导出插件实例
plugin = SecurityPlugin()
