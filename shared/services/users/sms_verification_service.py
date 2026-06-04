"""
手机短信验证服务
提供手机号验证码发送、验证等功能
支持多种SMS服务商集成
"""


import random
import string
from datetime import datetime, timedelta
from typing import Optional, Dict

from src.unified_logger import default_logger as logger


class SMSVerificationService:
    """手机短信验证服务"""

    # 配置常量
    CODE_LENGTH = 6  # 验证码长度
    EXPIRE_MINUTES = 10  # 验证码有效期(分钟)
    MAX_ATTEMPTS = 5  # 最大验证尝试次数
    RESEND_INTERVAL_SECONDS = 60  # 重发间隔(秒)

    # 中国手机号正则
    PHONE_PATTERN = r'^1[3-9]\d{9}$'

    def __init__(self):
        # 使用内存存储验证码(生产环境应使用Redis)
        self._verification_codes = {}

        # SMS服务商配置
        self.sms_config = {
            'provider': 'mock',  # mock, aliyun, tencent, twilio
            'access_key': '',
            'secret_key': '',
            'sign_name': 'FastBlog',
            'template_code': 'SMS_123456789',
        }

        # 频率限制
        self._send_history = {}  # {phone: [timestamp1, timestamp2, ...]}
        self.max_daily_sends = 10  # 每日最大发送次数

    def validate_phone_format(self, phone: str) -> bool:
        """
        验证手机号格式
        
        Args:
            phone: 手机号
            
        Returns:
            是否为有效手机号格式
        """
        import re
        return bool(re.match(self.PHONE_PATTERN, phone))

    def generate_code(self) -> str:
        """生成随机验证码"""
        return ''.join(random.choices(string.digits, k=self.CODE_LENGTH))

    def _check_rate_limit(self, phone: str) -> Optional[str]:
        """
        检查发送频率限制
        
        Args:
            phone: 手机号
            
        Returns:
            如果受限返回错误消息,否则返回None
        """
        now = datetime.now()

        # 初始化记录
        if phone not in self._send_history:
            self._send_history[phone] = []

        # 清理24小时前的记录
        cutoff = now - timedelta(hours=24)
        self._send_history[phone] = [
            ts for ts in self._send_history[phone]
            if ts > cutoff
        ]

        # 检查每日限制
        if len(self._send_history[phone]) >= self.max_daily_sends:
            return f'今日发送次数已达上限({self.max_daily_sends}次),请明天再试'

        # 检查重发间隔
        if self._send_history[phone]:
            last_send = max(self._send_history[phone])
            elapsed = (now - last_send).total_seconds()

            if elapsed < self.RESEND_INTERVAL_SECONDS:
                remaining = int(self.RESEND_INTERVAL_SECONDS - elapsed)
                return f'请稍后再试,{remaining}秒后可重新发送'

        return None

    def _send_sms_mock(self, phone: str, code: str) -> bool:
        """
        模拟发送短信(开发/测试环境)
        
        Args:
            phone: 手机号
            code: 验证码
            
        Returns:
            是否发送成功
        """
        logger.info(f"[SMS MOCK] Phone: {phone}, Code: {code}")
        print(f"\n{'=' * 60}")
        print(f"📱 短信验证码 (MOCK模式)")
        print(f"手机号: {phone}")
        print(f"验证码: {code}")
        print(f"有效期: {self.EXPIRE_MINUTES} 分钟")
        print(f"{'=' * 60}\n")
        return True

    def _send_sms_aliyun(self, phone: str, code: str) -> bool:
        """
        使用阿里云SMS发送验证码
        
        Args:
            phone: 手机号
            code: 验证码
            
        Returns:
            是否发送成功
        """
        try:
            import json
            from alibabacloud_dysmsapi20170525.client import Client as DysmsapiClient
            from alibabacloud_tea_openapi import models as open_api_models
            from alibabacloud_dysmsapi20170525 import models as dysmsapi_models
            from alibabacloud_tea_util import models as util_models

            access_key_id = self.sms_config.get('aliyun_access_key_id', '')
            access_key_secret = self.sms_config.get('aliyun_access_key_secret', '')
            sign_name = self.sms_config.get('aliyun_sign_name', '')
            template_code = self.sms_config.get('aliyun_template_code', '')

            if not all([access_key_id, access_key_secret, sign_name, template_code]):
                logger.warning("Aliyun SMS config incomplete, using mock mode")
                return self._send_sms_mock(phone, code)

            config = open_api_models.Config(
                access_key_id=access_key_id,
                access_key_secret=access_key_secret
            )
            config.endpoint = 'dysmsapi.aliyuncs.com'
            client = DysmsapiClient(config)

            send_sms_request = dysmsapi_models.SendSmsRequest(
                phone_numbers=phone,
                sign_name=sign_name,
                template_code=template_code,
                template_param=json.dumps({'code': code})
            )

            runtime = util_models.RuntimeOptions()
            response = client.send_sms_with_options(send_sms_request, runtime)

            if response.body.code == 'OK':
                logger.info(f"SMS sent successfully via Aliyun to {phone}")
                return True
            else:
                logger.error(f"Aliyun SMS failed: {response.body.message}")
                return False

        except ImportError:
            logger.warning("Aliyun SDK not installed, using mock mode")
            return self._send_sms_mock(phone, code)
        except Exception as e:
            logger.error(f"Failed to send SMS via Aliyun: {str(e)}")
            return False

    def _send_sms_tencent(self, phone: str, code: str) -> bool:
        """
        使用腾讯云SMS发送验证码
        
        Args:
            phone: 手机号
            code: 验证码
            
        Returns:
            是否发送成功
        """
        try:
            from tencentcloud.common import credential
            from tencentcloud.common.profile.client_profile import ClientProfile
            from tencentcloud.common.profile.http_profile import HttpProfile
            from tencentcloud.sms.v20210111 import sms_client, models

            secret_id = self.sms_config.get('tencent_secret_id', '')
            secret_key = self.sms_config.get('tencent_secret_key', '')
            sdk_app_id = self.sms_config.get('tencent_sdk_app_id', '')
            sign_name = self.sms_config.get('tencent_sign_name', '')
            template_id = self.sms_config.get('tencent_template_id', '')

            if not all([secret_id, secret_key, sdk_app_id, sign_name, template_id]):
                logger.warning("Tencent SMS config incomplete, using mock mode")
                return self._send_sms_mock(phone, code)

            cred = credential.Credential(secret_id, secret_key)
            http_profile = HttpProfile()
            http_profile.endpoint = "sms.tencentcloudapi.com"

            client_profile = ClientProfile()
            client_profile.httpProfile = http_profile
            client = sms_client.SmsClient(cred, "ap-guangzhou", client_profile)

            req = models.SendSmsRequest()
            req.SmsSdkAppId = sdk_app_id
            req.SignName = sign_name
            req.TemplateId = template_id
            req.TemplateParamSet = [code]
            req.PhoneNumberSet = [phone]

            resp = client.SendSms(req)

            if resp.SendStatusSet and resp.SendStatusSet[0].Code == 'Ok':
                logger.info(f"SMS sent successfully via Tencent to {phone}")
                return True
            else:
                error_msg = resp.SendStatusSet[0].Message if resp.SendStatusSet else 'Unknown error'
                logger.error(f"Tencent SMS failed: {error_msg}")
                return False

        except ImportError:
            logger.warning("Tencent SDK not installed, using mock mode")
            return self._send_sms_mock(phone, code)
        except Exception as e:
            logger.error(f"Failed to send SMS via Tencent: {str(e)}")
            return False

    def _send_sms_twilio(self, phone: str, code: str) -> bool:
        """
        使用Twilio发送验证码(国际短信)
        
        Args:
            phone: 手机号(需带国家代码,如+86)
            code: 验证码
            
        Returns:
            是否发送成功
        """
        try:
            from twilio.rest import Client

            account_sid = self.sms_config.get('twilio_account_sid', '')
            auth_token = self.sms_config.get('twilio_auth_token', '')
            from_number = self.sms_config.get('twilio_from_number', '')

            if not all([account_sid, auth_token, from_number]):
                logger.warning("Twilio SMS config incomplete, using mock mode")
                return self._send_sms_mock(phone, code)

            client = Client(account_sid, auth_token)

            message = client.messages.create(
                body=f'Your verification code is: {code}',
                from_=from_number,
                to=phone
            )

            if message.sid:
                logger.info(f"SMS sent successfully via Twilio to {phone}, SID: {message.sid}")
                return True
            else:
                logger.error("Twilio SMS failed: No message SID returned")
                return False

        except ImportError:
            logger.warning("Twilio SDK not installed, using mock mode")
            return self._send_sms_mock(phone, code)
        except Exception as e:
            logger.error(f"Failed to send SMS via Twilio: {str(e)}")
            return False

    def _send_sms(self, phone: str, code: str) -> bool:
        """
        根据配置选择SMS服务商发送短信
        
        Args:
            phone: 手机号
            code: 验证码
            
        Returns:
            是否发送成功
        """
        provider = self.sms_config.get('provider', 'mock')

        if provider == 'aliyun':
            return self._send_sms_aliyun(phone, code)
        elif provider == 'tencent':
            return self._send_sms_tencent(phone, code)
        elif provider == 'twilio':
            return self._send_sms_twilio(phone, code)
        else:
            # 默认使用模拟模式
            return self._send_sms_mock(phone, code)

    def send_verification_code(self, phone: str) -> dict:
        """
        发送手机验证码
        
        Args:
            phone: 手机号
            
        Returns:
            包含成功状态和消息的字典
        """
        # 验证手机号格式
        if not self.validate_phone_format(phone):
            return {
                'success': False,
                'message': '手机号格式不正确'
            }

        # 检查频率限制
        rate_limit_msg = self._check_rate_limit(phone)
        if rate_limit_msg:
            return {
                'success': False,
                'message': rate_limit_msg
            }

        # 生成验证码
        code = self.generate_code()

        # 发送短信
        send_success = self._send_sms(phone, code)

        if not send_success:
            return {
                'success': False,
                'message': '短信发送失败,请稍后重试'
            }

        # 记录发送历史
        self._send_history[phone].append(datetime.now())

        # 存储验证码
        self._verification_codes[phone] = {
            'code': code,
            'sent_at': datetime.now(),
            'attempts': 0,
            'verified': False
        }

        return {
            'success': True,
            'message': '验证码已发送到您的手机',
            'expire_minutes': self.EXPIRE_MINUTES
        }

    def verify_code(self, phone: str, code: str) -> dict:
        """
        验证手机验证码
        
        Args:
            phone: 手机号
            code: 验证码
            
        Returns:
            包含验证结果的字典
        """
        # 检查是否有验证码记录
        if phone not in self._verification_codes:
            return {
                'success': False,
                'message': '请先获取验证码'
            }

        record = self._verification_codes[phone]

        # 检查是否已验证
        if record['verified']:
            return {
                'success': False,
                'message': '该验证码已被使用'
            }

        # 检查尝试次数
        if record['attempts'] >= self.MAX_ATTEMPTS:
            return {
                'success': False,
                'message': '验证次数过多,请重新获取验证码'
            }

        # 检查是否过期
        elapsed = (datetime.now() - record['sent_at']).total_seconds()
        if elapsed > self.EXPIRE_MINUTES * 60:
            # 清除过期的验证码
            del self._verification_codes[phone]
            return {
                'success': False,
                'message': '验证码已过期,请重新获取'
            }

        # 增加尝试次数
        record['attempts'] += 1

        # 验证验证码
        if record['code'] != code:
            remaining_attempts = self.MAX_ATTEMPTS - record['attempts']
            return {
                'success': False,
                'message': f'验证码错误,还剩 {remaining_attempts} 次机会',
                'remaining_attempts': remaining_attempts
            }

        # 验证成功
        record['verified'] = True
        record['verified_at'] = datetime.now()

        return {
            'success': True,
            'message': '验证成功'
        }

    def is_verified(self, phone: str) -> bool:
        """
        检查手机号是否已验证
        
        Args:
            phone: 手机号
            
        Returns:
            是否已验证
        """
        if phone not in self._verification_codes:
            return False

        return self._verification_codes[phone].get('verified', False)

    def cleanup_expired_codes(self) -> int:
        """
        清理过期的验证码
        
        Returns:
            清理的数量
        """
        now = datetime.now()
        expired_phones = []

        for phone, record in self._verification_codes.items():
            elapsed = (now - record['sent_at']).total_seconds()
            if elapsed > self.EXPIRE_MINUTES * 60:
                expired_phones.append(phone)

        for phone in expired_phones:
            del self._verification_codes[phone]

        logger.info(f"Cleaned up {len(expired_phones)} expired SMS verification codes")
        return len(expired_phones)

    def configure_sms_provider(self, provider: str, access_key: str = '',
                               secret_key: str = '', sign_name: str = 'FastBlog',
                               template_code: str = ''):
        """
        配置SMS服务商
        
        Args:
            provider: 服务商名称 (mock, aliyun, tencent, twilio)
            access_key: Access Key
            secret_key: Secret Key
            sign_name: 签名名称
            template_code: 模板代码
        """
        self.sms_config.update({
            'provider': provider,
            'access_key': access_key,
            'secret_key': secret_key,
            'sign_name': sign_name,
            'template_code': template_code,
        })
        logger.info(f"SMS provider configured: {provider}")


# 全局实例
sms_verification_service = SMSVerificationService()
