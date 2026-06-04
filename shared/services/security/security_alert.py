"""
安全事件告警服务

提供多种告警渠道（邮件、短信、Webhook）
支持自定义告警规则
"""

import json
import smtplib
from datetime import datetime
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from typing import Any, Dict, List, Optional

import aiohttp


class AlertChannel:
    """告警渠道基类"""

    async def send_alert(self, alert_data: Dict[str, Any]) -> bool:
        """发送告警"""
        raise NotImplementedError


class EmailAlertChannel(AlertChannel):
    """邮件告警渠道"""

    def __init__(
            self,
            smtp_server: str,
            smtp_port: int,
            username: str,
            password: str,
            from_email: str,
            to_emails: List[str],
            use_tls: bool = True
    ):
        self.smtp_server = smtp_server
        self.smtp_port = smtp_port
        self.username = username
        self.password = password
        self.from_email = from_email
        self.to_emails = to_emails
        self.use_tls = use_tls

    async def send_alert(self, alert_data: Dict[str, Any]) -> bool:
        """发送邮件告警"""
        try:
            msg = MIMEMultipart()
            msg['From'] = self.from_email
            msg['To'] = ', '.join(self.to_emails)
            msg['Subject'] = f"[安全告警] {alert_data.get('title', 'Unknown')}"

            # 构建HTML内容
            html_content = f"""
            <html>
            <body>
                <h2 style="color: #d32f2f;">{alert_data.get('title', '安全告警')}</h2>
                <p><strong>类型:</strong> {alert_data.get('type', 'N/A')}</p>
                <p><strong>严重程度:</strong> {alert_data.get('severity', 'N/A')}</p>
                <p><strong>时间:</strong> {alert_data.get('timestamp', datetime.now().isoformat())}</p>
                <p><strong>消息:</strong> {alert_data.get('message', 'N/A')}</p>
                
                <h3>详细信息:</h3>
                <pre>{json.dumps(alert_data.get('details', {}), indent=2)}</pre>
                
                <hr>
                <p style="color: #666; font-size: 12px;">此邮件由FastBlog安全监控系统自动发送</p>
            </body>
            </html>
            """

            msg.attach(MIMEText(html_content, 'html'))

            # 发送邮件
            server = smtplib.SMTP(self.smtp_server, self.smtp_port)
            if self.use_tls:
                server.starttls()
            server.login(self.username, self.password)
            server.sendmail(self.from_email, self.to_emails, msg.as_string())
            server.quit()

            return True
        except Exception as e:
            print(f"Failed to send email alert: {e}")
            return False


class WebhookAlertChannel(AlertChannel):
    """Webhook告警渠道"""

    def __init__(self, webhook_url: str, headers: Optional[Dict[str, str]] = None):
        self.webhook_url = webhook_url
        self.headers = headers or {'Content-Type': 'application/json'}

    async def send_alert(self, alert_data: Dict[str, Any]) -> bool:
        """发送Webhook告警"""
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(
                        self.webhook_url,
                        headers=self.headers,
                        json=alert_data,
                        timeout=aiohttp.ClientTimeout(total=10)
                ) as response:
                    return response.status == 200
        except Exception as e:
            print(f"Failed to send webhook alert: {e}")
            return False


class SMSAlertChannel(AlertChannel):
    """短信告警渠道（示例实现）"""

    def __init__(self, api_key: str, phone_numbers: List[str], provider: str = 'aliyun', **kwargs):
        """
        初始化短信渠道
        
        Args:
            api_key: API密钥
            phone_numbers: 手机号列表
            provider: 短信服务商 (aliyun, tencent, twilio)
            **kwargs: 其他配置参数
        """
        self.api_key = api_key
        self.phone_numbers = phone_numbers
        self.provider = provider
        self.config = kwargs

    async def send_alert(self, alert_data: Dict[str, Any]) -> bool:
        """发送短信告警"""
        try:
            message = f"[安全告警] {alert_data.get('title')}: {alert_data.get('message')}"

            # 根据服务商调用不同的API
            if self.provider == 'aliyun':
                return await self._send_via_aliyun(message)
            elif self.provider == 'tencent':
                return await self._send_via_tencent(message)
            elif self.provider == 'twilio':
                return await self._send_via_twilio(message)
            else:
                print(f"Unsupported SMS provider: {self.provider}")
                return False

        except Exception as e:
            print(f"Failed to send SMS alert: {e}")
            return False

    async def _send_via_aliyun(self, message: str) -> bool:
        """通过阿里云短信服务发送"""
        try:
            import aiohttp
            from aliyunsdkcore.client import AcsClient
            from aliyunsdkcore.request import CommonRequest

            # 获取配置
            access_key_id = self.config.get('access_key_id', '')
            access_key_secret = self.config.get('access_key_secret', '')
            sign_name = self.config.get('sign_name', '')
            template_code = self.config.get('template_code', '')
            region_id = self.config.get('region_id', 'cn-hangzhou')

            if not all([access_key_id, access_key_secret, sign_name, template_code]):
                print("Aliyun SMS configuration incomplete")
                return False

            # 创建客户端
            client = AcsClient(access_key_id, access_key_secret, region_id)

            # 构建请求
            request = CommonRequest()
            request.set_accept_format('json')
            request.set_domain('dysmsapi.aliyuncs.com')
            request.set_method('POST')
            request.set_protocol_type('https')
            request.set_version('2017-05-25')
            request.set_action_name('SendSms')

            # 添加参数
            request.add_query_param('PhoneNumbers', ','.join(self.phone_numbers))
            request.add_query_param('SignName', sign_name)
            request.add_query_param('TemplateCode', template_code)
            request.add_query_param('TemplateParam', f'{{"message":"{message}"}}')

            # 发送请求
            response = client.do_action_with_exception(request)
            print(f"Aliyun SMS sent successfully: {response}")
            return True

        except ImportError:
            print("aliyunsdkcore not installed. Install with: pip install aliyun-python-sdk-core")
            return False
        except Exception as e:
            print(f"Failed to send via Aliyun SMS: {e}")
            return False

    async def _send_via_tencent(self, message: str) -> bool:
        """通过腾讯云短信服务发送"""
        try:
            from tencentcloud.common import credential
            from tencentcloud.sms.v20210111 import sms_client, models

            # 获取配置
            secret_id = self.config.get('secret_id', '')
            secret_key = self.config.get('secret_key', '')
            sdk_app_id = self.config.get('sdk_app_id', '')
            sign_name = self.config.get('sign_name', '')
            template_id = self.config.get('template_id', '')
            region = self.config.get('region', 'ap-guangzhou')

            if not all([secret_id, secret_key, sdk_app_id, sign_name, template_id]):
                print("Tencent SMS configuration incomplete")
                return False

            # 创建客户端
            cred = credential.Credential(secret_id, secret_key)
            client = sms_client.SmsClient(cred, region)

            # 构建请求
            req = models.SendSmsRequest()
            req.PhoneNumberSet = self.phone_numbers
            req.SmsSdkAppId = sdk_app_id
            req.SignName = sign_name
            req.TemplateId = template_id
            req.TemplateParamSet = [message]

            # 发送请求
            resp = client.SendSms(req)
            print(f"Tencent SMS sent successfully: {resp.to_json_string()}")
            return True

        except ImportError:
            print("tencentcloud-sdk-python not installed. Install with: pip install tencentcloud-sdk-python")
            return False
        except Exception as e:
            print(f"Failed to send via Tencent SMS: {e}")
            return False

    async def _send_via_twilio(self, message: str) -> bool:
        """通过 Twilio 短信服务发送"""
        try:
            from twilio.rest import Client

            # 获取配置
            account_sid = self.config.get('account_sid', '')
            auth_token = self.config.get('auth_token', '')
            from_number = self.config.get('from_number', '')

            if not all([account_sid, auth_token, from_number]):
                print("Twilio configuration incomplete")
                return False

            # 创建客户端
            client = Client(account_sid, auth_token)

            # 发送短信到所有号码
            success_count = 0
            for phone_number in self.phone_numbers:
                try:
                    message_obj = client.messages.create(
                        body=message,
                        from_=from_number,
                        to=phone_number
                    )
                    print(f"Twilio SMS sent to {phone_number}: {message_obj.sid}")
                    success_count += 1
                except Exception as e:
                    print(f"Failed to send Twilio SMS to {phone_number}: {e}")

            return success_count > 0

        except ImportError:
            print("twilio not installed. Install with: pip install twilio")
            return False
        except Exception as e:
            print(f"Failed to send via Twilio: {e}")
            return False


class SecurityAlertService:
    """
    安全事件告警服务
    
    管理和发送安全告警
    """

    def __init__(self):
        """初始化告警服务"""
        self.channels: Dict[str, AlertChannel] = {}
        self.rules: List[Dict[str, Any]] = []
        self.alert_history: List[Dict[str, Any]] = []

        # 告警频率限制 {alert_type: last_sent_timestamp}
        self.rate_limits: Dict[str, datetime] = {}
        self.rate_limit_minutes = 5  # 同类型告警最小间隔5分钟

    def add_channel(self, channel_id: str, channel: AlertChannel):
        """
        添加告警渠道
        
        Args:
            channel_id: 渠道ID
            channel: 告警渠道实例
        """
        self.channels[channel_id] = channel

    def remove_channel(self, channel_id: str):
        """移除告警渠道"""
        if channel_id in self.channels:
            del self.channels[channel_id]

    def add_rule(
            self,
            rule_id: str,
            alert_type: str,
            severity: str,
            channels: List[str],
            enabled: bool = True
    ):
        """
        添加告警规则
        
        Args:
            rule_id: 规则ID
            alert_type: 告警类型
            severity: 严重程度 (low, medium, high, critical)
            channels: 使用的告警渠道列表
            enabled: 是否启用
        """
        self.rules.append({
            'rule_id': rule_id,
            'alert_type': alert_type,
            'severity': severity,
            'channels': channels,
            'enabled': enabled,
        })

    async def send_alert(
            self,
            alert_type: str,
            title: str,
            message: str,
            severity: str = 'medium',
            details: Optional[Dict[str, Any]] = None,
            force_send: bool = False
    ) -> Dict[str, Any]:
        """
        发送告警
        
        Args:
            alert_type: 告警类型
            title: 标题
            message: 消息
            severity: 严重程度
            details: 详细信息
            force_send: 强制发送（忽略频率限制）
        
        Returns:
            发送结果
        """
        # 检查频率限制
        if not force_send and not self._check_rate_limit(alert_type):
            return {
                'success': False,
                'message': 'Rate limit exceeded',
                'skipped': True,
            }

        # 构建告警数据
        alert_data = {
            'type': alert_type,
            'title': title,
            'message': message,
            'severity': severity,
            'timestamp': datetime.now().isoformat(),
            'details': details or {},
        }

        # 查找匹配的规则
        matching_rules = [
            rule for rule in self.rules
            if rule['alert_type'] == alert_type and
               rule['severity'] == severity and
               rule['enabled']
        ]

        if not matching_rules:
            # 如果没有匹配规则，使用默认渠道
            channels_to_use = list(self.channels.keys())
        else:
            # 收集所有渠道
            channels_to_use = set()
            for rule in matching_rules:
                channels_to_use.update(rule['channels'])

        # 发送到所有渠道
        results = {}
        for channel_id in channels_to_use:
            if channel_id in self.channels:
                success = await self.channels[channel_id].send_alert(alert_data)
                results[channel_id] = success

        # 记录历史
        alert_data['sent_to'] = list(channels_to_use)
        alert_data['results'] = results
        self.alert_history.append(alert_data)

        # 更新频率限制
        self.rate_limits[alert_type] = datetime.now()

        return {
            'success': any(results.values()),
            'results': results,
            'alert_data': alert_data,
        }

    def _check_rate_limit(self, alert_type: str) -> bool:
        """
        检查频率限制
        
        Args:
            alert_type: 告警类型
        
        Returns:
            是否可以发送
        """
        if alert_type not in self.rate_limits:
            return True

        last_sent = self.rate_limits[alert_type]
        elapsed = (datetime.now() - last_sent).total_seconds() / 60

        return elapsed >= self.rate_limit_minutes

    def get_alert_history(
            self,
            hours: int = 24,
            alert_type: Optional[str] = None,
            severity: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        获取告警历史
        
        Args:
            hours: 最近多少小时
            alert_type: 告警类型过滤
            severity: 严重程度过滤
        
        Returns:
            告警历史列表
        """
        cutoff = datetime.now().timestamp() - (hours * 3600)

        filtered = []
        for alert in self.alert_history:
            alert_time = datetime.fromisoformat(alert['timestamp']).timestamp()

            if alert_time < cutoff:
                continue

            if alert_type and alert['type'] != alert_type:
                continue

            if severity and alert['severity'] != severity:
                continue

            filtered.append(alert)

        # 按时间排序
        filtered.sort(key=lambda x: x['timestamp'], reverse=True)

        return filtered

    def get_statistics(self, hours: int = 24) -> Dict[str, Any]:
        """
        获取告警统计
        
        Args:
            hours: 统计最近多少小时
        
        Returns:
            统计信息
        """
        history = self.get_alert_history(hours=hours)

        # 按类型统计
        by_type = {}
        for alert in history:
            alert_type = alert['type']
            if alert_type not in by_type:
                by_type[alert_type] = 0
            by_type[alert_type] += 1

        # 按严重程度统计
        by_severity = {}
        for alert in history:
            severity = alert['severity']
            if severity not in by_severity:
                by_severity[severity] = 0
            by_severity[severity] += 1

        return {
            'period_hours': hours,
            'total_alerts': len(history),
            'by_type': by_type,
            'by_severity': by_severity,
            'channels_configured': len(self.channels),
            'rules_configured': len(self.rules),
        }

    def update_rate_limit(self, minutes: int):
        """
        更新频率限制
        
        Args:
            minutes: 最小间隔分钟数
        """
        self.rate_limit_minutes = minutes


# 全局实例
security_alert_service = SecurityAlertService()

# 导出
__all__ = ['SecurityAlertService', 'security_alert_service', 'EmailAlertChannel', 'WebhookAlertChannel',
           'SMSAlertChannel']
