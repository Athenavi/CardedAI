"""
FastBlog Cloud SSL 证书管理插件
自动申请、续期和部署 Let's Encrypt 证书
"""

import asyncio
import shutil
import subprocess
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any, Optional

from shared.services.plugins.plugin_manager.core import BasePlugin, plugin_hooks


class SSLCertificatePlugin(BasePlugin):
    """
    FastBlog Cloud SSL 证书管理插件

    功能:
    1. Let's Encrypt 证书自动申请
    2. HTTP-01 和 DNS-01 验证
    3. 证书自动续期
    4. Nginx/Apache 自动部署
    5. 多域名和通配符证书支持
    6. 证书监控和告警
    7. SSL 配置优化建议
    """

    def __init__(self):
        super().__init__(
            plugin_id=0,
            name="FastBlog Cloud SSL",
            slug="cloud-ssl",
            version="1.0.0"
        )

        # 默认设置
        self.settings = {
            'enabled': False,

            # ACME 配置
            'acme': {
                'email': '',  # Let's Encrypt 注册邮箱
                'server': 'production',  # production/staging
                'agree_tos': True,
            },

            # 证书配置
            'certificates': [],

            # 验证方法
            'validation': {
                'method': 'http-01',  # http-01/dns-01
                'dns_provider': '',  # cloudflare/aliyun/tencent (DNS-01需要)
                'dns_credentials': {},
            },

            # 自动续期
            'auto_renewal': {
                'enabled': True,
                'check_interval_days': 7,
                'renew_before_days': 30,  # 到期前30天续期
            },

            # Web 服务器配置
            'web_server': {
                'type': 'nginx',  # nginx/apache
                'config_dir': '/etc/nginx',
                'reload_command': 'systemctl reload nginx',
                'test_command': 'nginx -t',
            },

            # 证书存储
            'storage': {
                'cert_dir': '/etc/letsencrypt/live',
                'backup_enabled': True,
                'backup_dir': 'backups/ssl',
            },

            # 监控和告警
            'monitoring': {
                'enabled': True,
                'check_expiry_daily': True,
                'alert_before_days': [30, 14, 7, 1],
                'notification_channels': ['email'],
            },

            # SSL 优化
            'ssl_optimization': {
                'enable_hsts': True,
                'hsts_max_age': 31536000,
                'enable_ocsp_stapling': True,
                'prefer_server_ciphers': True,
                'min_tls_version': 'TLSv1.2',
            }
        }

        # 证书目录
        self.cert_dir = Path(self.settings['storage']['cert_dir'])
        self.backup_dir = Path(self.settings['storage']['backup_dir'])
        self.backup_dir.mkdir(parents=True, exist_ok=True)

        # 证书缓存
        self._certificate_cache: Dict[str, Dict] = {}

        print("[CloudSSL] Plugin initialized")

    def register_hooks(self):
        """注册钩子"""
        # 定时检查证书续期
        if self.settings['auto_renewal']['enabled']:
            plugin_hooks.add_action(
                "weekly_cleanup",
                self.check_and_renew_certificates,
                priority=5
            )

        # 每日检查证书过期
        if self.settings['monitoring']['enabled'] and self.settings['monitoring']['check_expiry_daily']:
            plugin_hooks.add_action(
                "daily_cleanup",
                self.check_certificate_expiry,
                priority=10
            )

    def activate(self):
        """激活插件"""
        super().activate()

        # 检查 certbot 是否安装
        if not self._check_certbot_installed():
            print("[CloudSSL] Warning: certbot not found. Please install it first.")

        print("[CloudSSL] Plugin activated")

    def deactivate(self):
        """停用插件"""
        super().deactivate()
        print("[CloudSSL] Plugin deactivated")

    def _check_certbot_installed(self) -> bool:
        """检查 certbot 是否安装"""
        try:
            result = subprocess.run(
                ['certbot', '--version'],
                capture_output=True,
                text=True,
                timeout=5
            )
            return result.returncode == 0
        except:
            return False

    async def request_certificate(
            self,
            domain: str,
            email: str = None,
            validation_method: str = None,
            wildcard: bool = False,
            additional_domains: List[str] = None
    ) -> Dict[str, Any]:
        """
        申请 SSL 证书

        Args:
            domain: 主域名
            email: 联系邮箱
            validation_method: 验证方法 (http-01/dns-01)
            wildcard: 是否通配符证书
            additional_domains: 额外域名 (SAN)

        Returns:
            申请结果
        """
        if not self.settings['enabled']:
            return {
                'success': False,
                'error': 'SSL plugin is not enabled'
            }

        if not self._check_certbot_installed():
            return {
                'success': False,
                'error': 'certbot is not installed'
            }

        # 使用配置的邮箱或传入的邮箱
        acme_email = email or self.settings['acme']['email']
        if not acme_email:
            return {
                'success': False,
                'error': 'ACME email not configured'
            }

        # 确定验证方法
        method = validation_method or self.settings['validation']['method']

        # 构建域名列表
        domains = [domain]
        if additional_domains:
            domains.extend(additional_domains)

        # 如果是通配符,添加 *.domain
        if wildcard:
            wildcard_domain = f"*.{domain}"
            if wildcard_domain not in domains:
                domains.insert(0, wildcard_domain)

        # 确定 ACME 服务器
        server = self.settings['acme']['server']
        acme_server = 'https://acme-v02.api.letsencrypt.org/directory' if server == 'production' else 'https://acme-staging-v02.api.letsencrypt.org/directory'

        try:
            # 构建 certbot 命令
            cmd = [
                'certbot', 'certonly',
                '--non-interactive',
                '--agree-tos',
                '-m', acme_email,
                '--server', acme_server,
            ]

            # 添加域名
            for d in domains:
                cmd.extend(['-d', d])

            # 根据验证方法添加参数
            if method == 'http-01':
                cmd.extend([
                    '--webroot',
                    '--webroot-path', '/var/www/html'  # 需要根据实际配置调整
                ])
            elif method == 'dns-01':
                dns_provider = self.settings['validation']['dns_provider']
                if not dns_provider:
                    return {
                        'success': False,
                        'error': 'DNS provider not configured for DNS-01 validation'
                    }

                cmd.extend([
                    f'--dns-{dns_provider}',
                    f'--dns-{dns_provider}-credentials',
                    f'/etc/letsencrypt/{dns_provider}-credentials.ini'
                ])

            # 执行 certbot
            print(f"[CloudSSL] Requesting certificate for: {', '.join(domains)}")

            loop = asyncio.get_event_loop()
            result = await loop.run_in_executor(
                None,
                lambda: subprocess.run(
                    cmd,
                    capture_output=True,
                    text=True,
                    timeout=300
                )
            )

            if result.returncode == 0:
                # 证书申请成功
                cert_info = await self._get_certificate_info(domain)

                # 备份证书
                if self.settings['storage']['backup_enabled']:
                    await self._backup_certificate(domain)

                # 部署到 Web 服务器
                deploy_result = await self.deploy_certificate(domain)

                return {
                    'success': True,
                    'domain': domain,
                    'domains': domains,
                    'validation_method': method,
                    'certificate': cert_info,
                    'deployed': deploy_result['success'],
                    'message': 'Certificate requested and deployed successfully'
                }
            else:
                error_msg = result.stderr.strip()
                print(f"[CloudSSL] Certificate request failed: {error_msg}")

                return {
                    'success': False,
                    'error': error_msg,
                    'stdout': result.stdout
                }

        except Exception as e:
            print(f"[CloudSSL] Certificate request exception: {e}")
            import traceback
            traceback.print_exc()

            return {
                'success': False,
                'error': str(e)
            }

    async def renew_certificate(self, domain: str) -> Dict[str, Any]:
        """
        续期 SSL 证书

        Args:
            domain: 域名

        Returns:
            续期结果
        """
        if not self._check_certbot_installed():
            return {
                'success': False,
                'error': 'certbot is not installed'
            }

        try:
            cmd = [
                'certbot', 'renew',
                '--cert-name', domain,
                '--non-interactive',
            ]

            print(f"[CloudSSL] Renewing certificate for: {domain}")

            loop = asyncio.get_event_loop()
            result = await loop.run_in_executor(
                None,
                lambda: subprocess.run(
                    cmd,
                    capture_output=True,
                    text=True,
                    timeout=300
                )
            )

            if result.returncode == 0:
                # 备份旧证书
                if self.settings['storage']['backup_enabled']:
                    await self._backup_certificate(domain)

                # 重新部署
                deploy_result = await self.deploy_certificate(domain)

                return {
                    'success': True,
                    'domain': domain,
                    'deployed': deploy_result['success'],
                    'message': 'Certificate renewed successfully'
                }
            else:
                return {
                    'success': False,
                    'error': result.stderr.strip()
                }

        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }

    async def check_and_renew_certificates(self):
        """检查并续期即将过期的证书"""
        print("[CloudSSL] Checking certificates for renewal...")

        renewed_count = 0

        for cert_config in self.settings['certificates']:
            domain = cert_config['domain']

            # 检查证书状态
            cert_info = await self._get_certificate_info(domain)

            if not cert_info:
                continue

            # 检查是否需要续期
            if cert_info['needs_renewal']:
                print(f"[CloudSSL] Certificate for {domain} needs renewal")

                result = await self.renew_certificate(domain)

                if result['success']:
                    renewed_count += 1

                    # 发送通知
                    await self._send_notification(
                        'certificate_renewed',
                        {
                            'domain': domain,
                            'new_expiry': cert_info.get('valid_until'),
                        }
                    )

        if renewed_count > 0:
            print(f"[CloudSSL] Renewed {renewed_count} certificate(s)")
        else:
            print("[CloudSSL] No certificates need renewal")

    async def check_certificate_expiry(self):
        """检查证书过期时间并发送告警"""
        print("[CloudSSL] Checking certificate expiry...")

        for cert_config in self.settings['certificates']:
            domain = cert_config['domain']

            cert_info = await self._get_certificate_info(domain)

            if not cert_info:
                continue

            days_until_expiry = cert_info.get('days_until_expiry', 999)

            # 检查是否需要在告警时间点发送通知
            alert_days = self.settings['monitoring']['alert_before_days']

            if days_until_expiry in alert_days:
                await self._send_notification(
                    'certificate_expiring_soon',
                    {
                        'domain': domain,
                        'days_until_expiry': days_until_expiry,
                        'expiry_date': cert_info.get('valid_until'),
                    }
                )

            # 如果已过期,发送紧急告警
            if days_until_expiry < 0:
                await self._send_notification(
                    'certificate_expired',
                    {
                        'domain': domain,
                        'expired_days': abs(days_until_expiry),
                    },
                    severity='critical'
                )

    async def deploy_certificate(
            self,
            domain: str,
            web_server_type: str = None
    ) -> Dict[str, Any]:
        """
        部署证书到 Web 服务器

        Args:
            domain: 域名
            web_server_type: Web 服务器类型 (nginx/apache)

        Returns:
            部署结果
        """
        server_type = web_server_type or self.settings['web_server']['type']

        try:
            cert_path = self.cert_dir / domain / 'fullchain.pem'
            key_path = self.cert_dir / domain / 'privkey.pem'

            if not cert_path.exists() or not key_path.exists():
                return {
                    'success': False,
                    'error': f'Certificate files not found for {domain}'
                }

            if server_type == 'nginx':
                return await self._deploy_to_nginx(domain, cert_path, key_path)
            elif server_type == 'apache':
                return await self._deploy_to_apache(domain, cert_path, key_path)
            else:
                return {
                    'success': False,
                    'error': f'Unsupported web server: {server_type}'
                }

        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }

    async def _deploy_to_nginx(
            self,
            domain: str,
            cert_path: Path,
            key_path: Path
    ) -> Dict[str, Any]:
        """部署到 Nginx"""
        try:
            config_dir = Path(self.settings['web_server']['config_dir'])
            sites_available = config_dir / 'sites-available'
            sites_enabled = config_dir / 'sites-enabled'

            # 更新 Nginx 配置
            vhost_file = sites_available / f"{domain}.conf"

            if vhost_file.exists():
                # 读取现有配置
                with open(vhost_file, 'r') as f:
                    config = f.read()

                # 替换证书路径
                config = re.sub(
                    r'ssl_certificate\s+[^;]+;',
                    f'ssl_certificate {cert_path};',
                    config
                )
                config = re.sub(
                    r'ssl_certificate_key\s+[^;]+;',
                    f'ssl_certificate_key {key_path};',
                    config
                )

                # 添加 SSL 优化配置
                if self.settings['ssl_optimization']['enable_hsts']:
                    hsts_header = f'add_header Strict-Transport-Security "max-age={self.settings["ssl_optimization"]["hsts_max_age"]}" always;'
                    if 'Strict-Transport-Security' not in config:
                        config = config.replace('ssl_protocols', f'    {hsts_header}\n    ssl_protocols')

                # 写回配置
                with open(vhost_file, 'w') as f:
                    f.write(config)

                print(f"[CloudSSL] Updated Nginx config for {domain}")

            # 测试配置
            test_cmd = self.settings['web_server']['test_command']
            test_result = subprocess.run(
                test_cmd,
                shell=True,
                capture_output=True,
                text=True
            )

            if test_result.returncode != 0:
                return {
                    'success': False,
                    'error': f'Nginx config test failed: {test_result.stderr}'
                }

            # 重载 Nginx
            reload_cmd = self.settings['web_server']['reload_command']
            reload_result = subprocess.run(
                reload_cmd,
                shell=True,
                capture_output=True,
                text=True
            )

            if reload_result.returncode == 0:
                return {
                    'success': True,
                    'message': 'Certificate deployed to Nginx successfully'
                }
            else:
                return {
                    'success': False,
                    'error': f'Nginx reload failed: {reload_result.stderr}'
                }

        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }

    async def _deploy_to_apache(
            self,
            domain: str,
            cert_path: Path,
            key_path: Path
    ) -> Dict[str, Any]:
        """部署到 Apache"""
        import re

        try:
            # 查找 Apache 虚拟主机配置文件
            apache_sites_dir = Path('/etc/apache2/sites-available')
            vhost_candidates = [
                apache_sites_dir / f'{domain}.conf',
                apache_sites_dir / f'{domain}-ssl.conf',
                apache_sites_dir / '000-default.conf',
                apache_sites_dir / 'default-ssl.conf',
            ]

            vhost_file = None
            for candidate in vhost_candidates:
                if candidate.exists():
                    vhost_file = candidate
                    break

            if vhost_file is None:
                # 创建新的 SSL 虚拟主机配置
                vhost_file = apache_sites_dir / f'{domain}-ssl.conf'
                ssl_config = f"""<VirtualHost *:443>
    ServerName {domain}
    ServerAlias www.{domain}
    DocumentRoot /var/www/{domain}

    SSLEngine on
    SSLCertificateFile {cert_path}
    SSLCertificateKeyFile {key_path}
    SSLProtocol all -SSLv3 -TLSv1 -TLSv1.1
    SSLCipherSuite HIGH:!aNULL:!MD5

    <Directory /var/www/{domain}>
        AllowOverride All
        Require all granted
    </Directory>

    ErrorLog ${{APACHE_LOG_DIR}}/{domain}_error.log
    CustomLog ${{APACHE_LOG_DIR}}/{domain}_access.log combined
</VirtualHost>
"""
                with open(vhost_file, 'w') as f:
                    f.write(ssl_config)
            else:
                # 更新现有配置文件中的证书路径
                with open(vhost_file, 'r') as f:
                    config = f.read()

                config = re.sub(
                    r'SSLCertificateFile\s+[^\n]+',
                    f'SSLCertificateFile {cert_path}',
                    config
                )
                config = re.sub(
                    r'SSLCertificateKeyFile\s+[^\n]+',
                    f'SSLCertificateKeyFile {key_path}',
                    config
                )

                # 如果没有 SSLEngine，添加 SSL 配置块
                if 'SSLEngine' not in config:
                    ssl_block = f"""
    SSLEngine on
    SSLCertificateFile {cert_path}
    SSLCertificateKeyFile {key_path}
    SSLProtocol all -SSLv3 -TLSv1 -TLSv1.1
    SSLCipherSuite HIGH:!aNULL:!MD5
"""
                    config = config.replace('</VirtualHost>', f'{ssl_block}\n</VirtualHost>')

                # 添加 HSTS 头
                if self.settings['ssl_optimization']['enable_hsts']:
                    hsts_header = f'Header always set Strict-Transport-Security "max-age={self.settings["ssl_optimization"]["hsts_max_age"]}"'
                    if 'Strict-Transport-Security' not in config:
                        config = config.replace('</VirtualHost>', f'    {hsts_header}\n</VirtualHost>')

                with open(vhost_file, 'w') as f:
                    f.write(config)

            print(f"[CloudSSL] Updated Apache config for {domain}")

            # 启用 SSL 模块和站点
            for cmd in [
                ['a2enmod', 'ssl'],
                ['a2enmod', 'headers'],
                ['a2ensite', f'{domain}-ssl'],
            ]:
                try:
                    subprocess.run(cmd, capture_output=True, text=True, timeout=10)
                except Exception:
                    pass

            # 测试 Apache 配置
            test_result = subprocess.run(
                ['apachectl', 'configtest'],
                capture_output=True,
                text=True,
                timeout=15
            )

            if test_result.returncode != 0:
                return {
                    'success': False,
                    'error': f'Apache config test failed: {test_result.stderr}'
                }

            # 重载 Apache
            reload_result = subprocess.run(
                ['systemctl', 'reload', 'apache2'],
                capture_output=True,
                text=True,
                timeout=15
            )

            if reload_result.returncode == 0:
                return {
                    'success': True,
                    'message': 'Certificate deployed to Apache successfully'
                }
            else:
                return {
                    'success': False,
                    'error': f'Apache reload failed: {reload_result.stderr}'
                }

        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }

    async def _get_certificate_info(self, domain: str) -> Optional[Dict[str, Any]]:
        """获取证书信息"""
        try:
            cert_path = self.cert_dir / domain / 'fullchain.pem'

            if not cert_path.exists():
                return None

            # 使用 openssl 读取证书信息
            cmd = [
                'openssl', 'x509',
                '-in', str(cert_path),
                '-noout',
                '-dates',
                '-subject',
                '-issuer'
            ]

            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=10
            )

            if result.returncode != 0:
                return None

            # 解析输出
            info = {'domain': domain}

            for line in result.stdout.split('\n'):
                if line.startswith('notBefore='):
                    info['valid_from'] = line.split('=', 1)[1]
                elif line.startswith('notAfter='):
                    info['valid_until'] = line.split('=', 1)[1]

            # 计算剩余天数
            if 'valid_until' in info:
                expiry_date = datetime.strptime(info['valid_until'], '%b %d %H:%M:%S %Y %Z')
                days_until_expiry = (expiry_date - datetime.now()).days
                info['days_until_expiry'] = days_until_expiry
                info['needs_renewal'] = days_until_expiry <= self.settings['auto_renewal']['renew_before_days']

            return info

        except Exception as e:
            print(f"[CloudSSL] Failed to get certificate info: {e}")
            return None

    async def _backup_certificate(self, domain: str):
        """备份证书"""
        try:
            backup_subdir = self.backup_dir / domain / datetime.now().strftime('%Y%m%d_%H%M%S')
            backup_subdir.mkdir(parents=True, exist_ok=True)

            cert_dir = self.cert_dir / domain

            if cert_dir.exists():
                # 复制证书文件
                for file in cert_dir.iterdir():
                    if file.is_file():
                        shutil.copy2(file, backup_subdir / file.name)

                print(f"[CloudSSL] Backed up certificate for {domain}")

        except Exception as e:
            print(f"[CloudSSL] Failed to backup certificate: {e}")

    async def _send_notification(
            self,
            event_type: str,
            data: Dict[str, Any],
            severity: str = 'warning'
    ):
        """发送通知"""
        channels = self.settings['monitoring']['notification_channels']

        message = f"[SSL] {event_type}: {data}"

        if 'email' in channels:
            await self._send_email_notification(event_type, data, severity)

        if 'webhook' in channels:
            await self._send_webhook_notification(event_type, data, severity)

    async def _send_email_notification(self, event_type: str, data: Dict[str, Any], severity: str):
        """发送邮件通知"""
        try:
            from shared.services.notifications.email_service import EmailService

            email_service = EmailService()

            # 构建邮件主题和内容
            severity_icons = {
                'info': 'ℹ️',
                'warning': '⚠️',
                'error': '❌',
                'critical': '🚨'
            }
            icon = severity_icons.get(severity, '⚠️')

            subject = f'[FastBlog] SSL {icon} {event_type}'
            html_content = f"""
            <h2>{icon} SSL 通知 - {event_type}</h2>
            <p><strong>域名:</strong> {data.get('domain', 'N/A')}</p>
            <p><strong>事件类型:</strong> {event_type}</p>
            <p><strong>严重程度:</strong> {severity}</p>
            <p><strong>详细信息:</strong></p>
            <pre style="background: #f5f5f5; padding: 10px; border-radius: 4px;">{json.dumps(data, indent=2, ensure_ascii=False)}</pre>
            <p><strong>时间:</strong> {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
            """

            # 获取收件人邮箱
            to_email = os.getenv('ADMIN_EMAIL', '')
            if not to_email:
                print("[CloudSSL] Admin email not configured, skipping email notification")
                return

            # 发送邮件
            success = email_service.send_email(
                to_email=to_email,
                subject=subject,
                html_content=html_content
            )

            if success:
                print(f"[CloudSSL] Email notification sent to {to_email}")
            else:
                print(f"[CloudSSL] Failed to send email notification")

        except Exception as e:
            print(f"[CloudSSL] Email notification error: {e}")

    async def _send_webhook_notification(self, event_type: str, data: Dict[str, Any], severity: str):
        """发送 Webhook 通知"""
        webhook_url = self.settings['monitoring'].get('webhook_url', '')

        if not webhook_url:
            print("[CloudSSL] Webhook URL not configured")
            return

        import aiohttp

        payload = {
            'service': 'cloud-ssl',
            'event': event_type,
            'severity': severity,
            'data': data,
            'timestamp': datetime.now().isoformat()
        }

        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(webhook_url, json=payload) as response:
                    if response.status == 200:
                        print(f"[CloudSSL] Webhook notification sent successfully")
                    else:
                        print(f"[CloudSSL] Webhook returned status {response.status}")
        except Exception as e:
            print(f"[CloudSSL] Webhook notification failed: {e}")

    def list_certificates(self) -> List[Dict[str, Any]]:
        """列出所有证书"""
        certificates = []

        for cert_config in self.settings['certificates']:
            domain = cert_config['domain']
            cert_info = self._get_certificate_info_sync(domain)

            if cert_info:
                certificates.append(cert_info)

        return certificates

    def _get_certificate_info_sync(self, domain: str) -> Optional[Dict[str, Any]]:
        """同步获取证书信息"""
        try:
            cert_path = self.cert_dir / domain / 'fullchain.pem'

            if not cert_path.exists():
                return None

            cmd = [
                'openssl', 'x509',
                '-in', str(cert_path),
                '-noout',
                '-dates'
            ]

            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=10
            )

            if result.returncode != 0:
                return None

            info = {'domain': domain}

            for line in result.stdout.split('\n'):
                if line.startswith('notAfter='):
                    info['valid_until'] = line.split('=', 1)[1]

            if 'valid_until' in info:
                expiry_date = datetime.strptime(info['valid_until'], '%b %d %H:%M:%S %Y %Z')
                days_until_expiry = (expiry_date - datetime.now()).days
                info['days_until_expiry'] = days_until_expiry
                info['status'] = 'expired' if days_until_expiry < 0 else 'active'

            return info

        except:
            return None

    def get_settings_ui(self) -> Dict[str, Any]:
        """返回设置界面配置"""
        return {
            'fields': [
                {
                    'key': 'enabled',
                    'type': 'boolean',
                    'label': '启用 SSL 管理',
                },
                {
                    'key': 'acme.email',
                    'type': 'email',
                    'label': 'Let\'s Encrypt 邮箱',
                },
                {
                    'key': 'acme.server',
                    'type': 'select',
                    'label': 'ACME 服务器',
                    'options': [
                        {'value': 'production', 'label': '生产环境'},
                        {'value': 'staging', 'label': '测试环境'},
                    ],
                },
                {
                    'key': 'validation.method',
                    'type': 'select',
                    'label': '验证方法',
                    'options': [
                        {'value': 'http-01', 'label': 'HTTP-01 (文件验证)'},
                        {'value': 'dns-01', 'label': 'DNS-01 (DNS记录验证)'},
                    ],
                },
                {
                    'key': 'auto_renewal.enabled',
                    'type': 'boolean',
                    'label': '启用自动续期',
                },
                {
                    'key': 'web_server.type',
                    'type': 'select',
                    'label': 'Web 服务器类型',
                    'options': [
                        {'value': 'nginx', 'label': 'Nginx'},
                        {'value': 'apache', 'label': 'Apache'},
                    ],
                },
                {
                    'key': 'ssl_optimization.enable_hsts',
                    'type': 'boolean',
                    'label': '启用 HSTS',
                },
            ],
            'actions': [
                {
                    'type': 'button',
                    'label': '申请新证书',
                    'action': 'request_certificate',
                    'variant': 'default',
                },
                {
                    'type': 'button',
                    'label': '查看所有证书',
                    'action': 'list_certificates',
                    'variant': 'outline',
                },
            ]
        }


# 全局实例
plugin = SSLCertificatePlugin()
