"""
双因素认证(2FA)服务
基于TOTP(Time-based One-Time Password)实现
"""

import base64
import json
import secrets
from io import BytesIO
from typing import Dict, Any, Optional, List

import pyotp
import qrcode


class TwoFactorAuthService:
    """
    双因素认证服务
    
    功能:
    1. 生成TOTP密钥
    2. 生成QR码用于Google Authenticator等应用扫描
    3. 验证TOTP验证码
    4. 生成和管理备用码
    5. 启用/禁用2FA
    """

    def __init__(self):
        self.issuer = "Fast Blog"  # issuer名称
        self.totp_length = 6  # TOTP长度
        self.totp_interval = 30  # TOTP间隔(秒)
        self.backup_codes_count = 10  # 备用码数量

    def generate_totp_secret(self) -> str:
        """
        生成TOTP密钥
        
        Returns:
            Base32编码的密钥字符串
        """
        return pyotp.random_base32()

    def generate_qr_code(self, secret: str, username: str, email: str) -> Dict[str, Any]:
        """
        生成QR码图像(用于Google Authenticator等应用扫描)
        
        Args:
            secret: TOTP密钥
            username: 用户名
            email: 邮箱
            
        Returns:
            包含QR码图像的字典
        """
        # 创建TOTP URI
        totp_uri = pyotp.totp.TOTP(secret).provisioning_uri(
            name=email or username,
            issuer_name=self.issuer
        )

        # 生成QR码
        qr = qrcode.QRCode(
            version=1,
            error_correction=qrcode.constants.ERROR_CORRECT_L,
            box_size=10,
            border=4,
        )
        qr.add_data(totp_uri)
        qr.make(fit=True)

        # 转换为图像
        img = qr.make_image(fill_color="black", back_color="white")

        # 转换为base64
        buffer = BytesIO()
        img.save(buffer, format='PNG')
        qr_base64 = base64.b64encode(buffer.getvalue()).decode('utf-8')

        return {
            'qr_code': f"data:image/png;base64,{qr_base64}",
            'secret': secret,
            'uri': totp_uri,
            'manual_entry_key': secret  # 用于手动输入
        }

    def verify_totp(self, secret: str, token: str, window: int = 1) -> bool:
        """
        验证TOTP验证码
        
        Args:
            secret: TOTP密钥
            token: 用户输入的6位验证码
            window: 允许的时间窗口(前后几个周期)
            
        Returns:
            是否验证成功
        """
        try:
            totp = pyotp.TOTP(secret)
            return totp.verify(token, valid_window=window)
        except Exception as e:
            print(f"TOTP verification error: {e}")
            return False

    def generate_backup_codes(self, count: Optional[int] = None) -> List[str]:
        """
        生成备用码
        
        Args:
            count: 备用码数量
            
        Returns:
            备用码列表
        """
        if count is None:
            count = self.backup_codes_count

        # 生成随机备用码(8位数字)
        codes = []
        for _ in range(count):
            code = ''.join([str(secrets.randbelow(10)) for _ in range(8)])
            codes.append(code)

        return codes

    def hash_backup_codes(self, codes: List[str]) -> str:
        """
        哈希备用码(用于安全存储)
        
        Args:
            codes: 备用码列表
            
        Returns:
            JSON格式的哈希后备用码
        """
        import hashlib

        hashed_codes = []
        for code in codes:
            # 使用SHA256哈希
            hashed = hashlib.sha256(code.encode('utf-8')).hexdigest()
            hashed_codes.append(hashed)

        return json.dumps(hashed_codes)

    def verify_backup_code(self, stored_codes_json: str, input_code: str) -> bool:
        """
        验证备用码
        
        Args:
            stored_codes_json: 存储的哈希后备用码JSON
            input_code: 用户输入的备用码
            
        Returns:
            是否验证成功
        """
        try:
            import hashlib

            hashed_codes = json.loads(stored_codes_json)
            input_hashed = hashlib.sha256(input_code.encode('utf-8')).hexdigest()

            if input_hashed in hashed_codes:
                # 移除已使用的备用码
                hashed_codes.remove(input_hashed)
                return True

            return False
        except Exception as e:
            print(f"Backup code verification error: {e}")
            return False

    def enable_2fa(self, user_id: int, secret: str, backup_codes: List[str], db_session) -> Dict[str, Any]:
        """
        为用户启用2FA
        
        Args:
            user_id: 用户ID
            secret: TOTP密钥
            backup_codes: 备用码列表
            db_session: 数据库会话
            
        Returns:
            操作结果
        """
        try:
            from sqlalchemy import select
            from shared.models.user import User

            # 查询用户
            query = select(User).where(User.id == user_id)
            result = db_session.execute(query)
            user = result.scalar_one_or_none()

            if not user:
                return {'success': False, 'error': '用户不存在'}

            # 更新用户2FA设置
            user.is_2fa_enabled = True
            user.totp_secret = secret
            user.backup_codes = self.hash_backup_codes(backup_codes)

            db_session.commit()

            return {
                'success': True,
                'message': '2FA已启用',
                'backup_codes': backup_codes  # 返回明文备用码供用户保存
            }
        except Exception as e:
            db_session.rollback()
            print(f"Enable 2FA error: {e}")
            return {'success': False, 'error': str(e)}

    def disable_2fa(self, user_id: int, db_session) -> Dict[str, Any]:
        """
        为用户禁用2FA
        
        Args:
            user_id: 用户ID
            db_session: 数据库会话
            
        Returns:
            操作结果
        """
        try:
            from sqlalchemy import select
            from shared.models.user import User

            query = select(User).where(User.id == user_id)
            result = db_session.execute(query)
            user = result.scalar_one_or_none()

            if not user:
                return {'success': False, 'error': '用户不存在'}

            # 清除2FA设置
            user.is_2fa_enabled = False
            user.totp_secret = None
            user.backup_codes = None

            db_session.commit()

            return {'success': True, 'message': '2FA已禁用'}
        except Exception as e:
            db_session.rollback()
            print(f"Disable 2FA error: {e}")
            return {'success': False, 'error': str(e)}

    def regenerate_backup_codes(self, user_id: int, db_session) -> Dict[str, Any]:
        """
        重新生成备用码
        
        Args:
            user_id: 用户ID
            db_session: 数据库会话
            
        Returns:
            新的备用码列表
        """
        try:
            from sqlalchemy import select
            from shared.models.user import User

            query = select(User).where(User.id == user_id)
            result = db_session.execute(query)
            user = result.scalar_one_or_none()

            if not user:
                return {'success': False, 'error': '用户不存在'}

            if not user.is_2fa_enabled:
                return {'success': False, 'error': '2FA未启用'}

            # 生成新的备用码
            new_codes = self.generate_backup_codes()
            user.backup_codes = self.hash_backup_codes(new_codes)

            db_session.commit()

            return {
                'success': True,
                'message': '备用码已重新生成',
                'backup_codes': new_codes
            }
        except Exception as e:
            db_session.rollback()
            print(f"Regenerate backup codes error: {e}")
            return {'success': False, 'error': str(e)}

    def verify_2fa_login(self, user_id: int, token: str, db_session) -> Dict[str, Any]:
        """
        验证2FA登录
        
        Args:
            user_id: 用户ID
            token: TOTP验证码或备用码
            db_session: 数据库会话
            
        Returns:
            验证结果
        """
        try:
            from sqlalchemy import select
            from shared.models.user import User

            query = select(User).where(User.id == user_id)
            result = db_session.execute(query)
            user = result.scalar_one_or_none()

            if not user:
                return {'success': False, 'error': '用户不存在'}

            if not user.is_2fa_enabled:
                return {'success': False, 'error': '2FA未启用'}

            # 首先尝试TOTP验证
            if user.totp_secret and self.verify_totp(user.totp_secret, token):
                return {'success': True, 'method': 'totp'}

            # 然后尝试备用码验证
            if user.backup_codes and self.verify_backup_code(user.backup_codes, token):
                # 更新备用码(移除已使用的)
                db_session.commit()
                return {'success': True, 'method': 'backup_code'}

            return {'success': False, 'error': '验证码错误'}
        except Exception as e:
            print(f"2FA login verification error: {e}")
            return {'success': False, 'error': str(e)}


# 全局实例
two_factor_auth = TwoFactorAuthService()
