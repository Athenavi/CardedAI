"""
时区和本地化服务
提供时区检测、日期格式化、货币符号等功能
"""


from datetime import datetime, timezone
from typing import Dict, List
from zoneinfo import ZoneInfo

from src.unified_logger import default_logger as logger


class LocalizationService:
    """时区和本地化服务"""

    def __init__(self):
        # 时区映射 {locale: timezone}
        self._timezone_map = {
            'zh-CN': 'Asia/Shanghai',
            'zh-TW': 'Asia/Taipei',
            'en-US': 'America/New_York',
            'en-GB': 'Europe/London',
            'ja-JP': 'Asia/Tokyo',
            'ko-KR': 'Asia/Seoul',
            'fr-FR': 'Europe/Paris',
            'de-DE': 'Europe/Berlin',
            'es-ES': 'Europe/Madrid',
            'pt-BR': 'America/Sao_Paulo',
            'ru-RU': 'Europe/Moscow',
            'ar-SA': 'Asia/Riyadh',
            'hi-IN': 'Asia/Kolkata',
        }

        # 日期格式模板
        self._date_formats = {
            'zh-CN': '%Y年%m月%d日',
            'zh-TW': '%Y年%m月%d日',
            'en-US': '%B %d, %Y',
            'en-GB': '%d %B %Y',
            'ja-JP': '%Y年%m月%d日',
            'ko-KR': '%Y년 %m월 %d일',
            'fr-FR': '%d %B %Y',
            'de-DE': '%d. %B %Y',
            'es-ES': '%d de %B de %Y',
            'pt-BR': '%d de %B de %Y',
            'ru-RU': '%d %B %Y г.',
            'ar-SA': '%d %B %Y',
            'hi-IN': '%d %B %Y',
        }

        # 日期时间格式模板
        self._datetime_formats = {
            'zh-CN': '%Y年%m月%d日 %H:%M',
            'zh-TW': '%Y年%m月%d日 %H:%M',
            'en-US': '%B %d, %Y %I:%M %p',
            'en-GB': '%d %B %Y %H:%M',
            'ja-JP': '%Y年%m月%d日 %H:%M',
            'ko-KR': '%Y년 %m월 %d일 %H:%M',
            'fr-FR': '%d %B %Y %H:%M',
            'de-DE': '%d. %B %Y %H:%M',
            'es-ES': '%d de %B de %Y %H:%M',
            'pt-BR': '%d de %B de %Y %H:%M',
            'ru-RU': '%d %B %Y г. %H:%M',
            'ar-SA': '%d %B %Y %H:%M',
            'hi-IN': '%d %B %Y %H:%M',
        }

        # 货币符号映射
        self._currency_symbols = {
            'zh-CN': '¥',
            'zh-TW': 'NT$',
            'en-US': '$',
            'en-GB': '£',
            'ja-JP': '¥',
            'ko-KR': '₩',
            'fr-FR': '€',
            'de-DE': '€',
            'es-ES': '€',
            'pt-BR': 'R$',
            'ru-RU': '₽',
            'ar-SA': '﷼',
            'hi-IN': '₹',
        }

        # 货币代码映射
        self._currency_codes = {
            'zh-CN': 'CNY',
            'zh-TW': 'TWD',
            'en-US': 'USD',
            'en-GB': 'GBP',
            'ja-JP': 'JPY',
            'ko-KR': 'KRW',
            'fr-FR': 'EUR',
            'de-DE': 'EUR',
            'es-ES': 'EUR',
            'pt-BR': 'BRL',
            'ru-RU': 'RUB',
            'ar-SA': 'SAR',
            'hi-IN': 'INR',
        }

        # 数字格式（千位分隔符和小数点）
        self._number_formats = {
            'zh-CN': {'thousands': ',', 'decimal': '.'},
            'en-US': {'thousands': ',', 'decimal': '.'},
            'en-GB': {'thousands': ',', 'decimal': '.'},
            'fr-FR': {'thousands': ' ', 'decimal': ','},
            'de-DE': {'thousands': '.', 'decimal': ','},
            'es-ES': {'thousands': '.', 'decimal': ','},
            'pt-BR': {'thousands': '.', 'decimal': ','},
            'ja-JP': {'thousands': ',', 'decimal': '.'},
            'ko-KR': {'thousands': ',', 'decimal': '.'},
            'ru-RU': {'thousands': ' ', 'decimal': ','},
            'ar-SA': {'thousands': ',', 'decimal': '.'},
            'hi-IN': {'thousands': ',', 'decimal': '.'},
        }

    def detect_timezone(self, ip_address: str = None,
                        locale: str = None) -> str:
        """
        检测用户时区

        Args:
            ip_address: IP地址(可选)
            locale: 语言区域(可选)

        Returns:
            时区名称
        """
        # 优先使用locale推断时区
        if locale and locale in self._timezone_map:
            return self._timezone_map[locale]

        # 根据IP地址检测时区
        if ip_address:
            try:
                timezone_from_ip = self._get_timezone_from_ip(ip_address)
                if timezone_from_ip:
                    return timezone_from_ip
            except Exception as e:
                logger.warning(f"Failed to detect timezone from IP: {e}")

        # 返回默认时区
        return 'UTC'

    def _get_timezone_from_ip(self, ip_address: str) -> str:
        """
        从IP地址获取时区

        Args:
            ip_address: IP地址

        Returns:
            时区名称，失败返回None
        """
        # 方法1: 使用 ipapi.co API (免费，无需API key)
        try:
            import urllib.request
            import json

            url = f"https://ipapi.co/{ip_address}/json/"
            response = urllib.request.urlopen(url, timeout=3)
            data = json.loads(response.read().decode('utf-8'))

            if 'timezone' in data and data['timezone']:
                logger.info(f"Detected timezone from IP {ip_address}: {data['timezone']}")
                return data['timezone']
        except Exception as e:
            logger.debug(f"ipapi.co failed: {e}")

        # 方法2: 使用 ipgeolocation.io API (需要API key)
        api_key = os.getenv('IPGEOLOCATION_API_KEY', '')
        if api_key:
            try:
                import urllib.request
                import json

                url = f"https://api.ipgeolocation.io/timezone?apiKey={api_key}&ip={ip_address}"
                response = urllib.request.urlopen(url, timeout=3)
                data = json.loads(response.read().decode('utf-8'))

                if 'timezone' in data and data['timezone']:
                    logger.info(f"Detected timezone from IP {ip_address}: {data['timezone']}")
                    return data['timezone']
            except Exception as e:
                logger.debug(f"ipgeolocation.io failed: {e}")

        # 方法3: 使用本地IP段映射（针对常见地区）
        timezone_by_ip_range = {
            # 中国
            'CN': 'Asia/Shanghai',
            # 美国
            'US': 'America/New_York',
            # 日本
            'JP': 'Asia/Tokyo',
            # 韩国
            'KR': 'Asia/Seoul',
            # 英国
            'GB': 'Europe/London',
            # 德国
            'DE': 'Europe/Berlin',
            # 法国
            'FR': 'Europe/Paris',
            # 澳大利亚
            'AU': 'Australia/Sydney',
        }

        # 简单的IP前缀判断（仅作为最后手段）
        if ip_address.startswith(('223.', '116.', '117.', '119.', '120.')):
            return 'Asia/Shanghai'
        elif ip_address.startswith(('8.', '9.', '10.', '11.')):
            return 'America/New_York'

        return None

    def convert_to_user_timezone(self, dt: datetime,
                                 user_timezone: str = 'UTC') -> datetime:
        """
        将UTC时间转换为用户本地时间

        Args:
            dt: UTC时间
            user_timezone: 用户时区

        Returns:
            用户本地时间
        """
        if dt.tzinfo is None:
            # 假设是UTC时间
            dt = dt.replace(tzinfo=timezone.utc)

        try:
            tz = ZoneInfo(user_timezone)
            return dt.astimezone(tz)
        except Exception as e:
            logger.error(f"Failed to convert timezone: {str(e)}")
            return dt

    def format_date(self, dt: datetime, locale: str = 'en-US',
                    user_timezone: str = 'UTC') -> str:
        """
        格式化日期

        Args:
            dt: 日期时间
            locale: 语言区域
            user_timezone: 用户时区

        Returns:
            格式化后的日期字符串
        """
        # 转换到用户时区
        local_dt = self.convert_to_user_timezone(dt, user_timezone)

        # 获取格式模板
        format_template = self._date_formats.get(locale, '%Y-%m-%d')

        try:
            return local_dt.strftime(format_template)
        except Exception as e:
            logger.error(f"Failed to format date: {str(e)}")
            return local_dt.strftime('%Y-%m-%d')

    def format_datetime(self, dt: datetime, locale: str = 'en-US',
                        user_timezone: str = 'UTC') -> str:
        """
        格式化日期时间

        Args:
            dt: 日期时间
            locale: 语言区域
            user_timezone: 用户时区

        Returns:
            格式化后的日期时间字符串
        """
        # 转换到用户时区
        local_dt = self.convert_to_user_timezone(dt, user_timezone)

        # 获取格式模板
        format_template = self._datetime_formats.get(locale, '%Y-%m-%d %H:%M:%S')

        try:
            return local_dt.strftime(format_template)
        except Exception as e:
            logger.error(f"Failed to format datetime: {str(e)}")
            return local_dt.strftime('%Y-%m-%d %H:%M:%S')

    def format_relative_time(self, dt: datetime, locale: str = 'en-US',
                             user_timezone: str = 'UTC') -> str:
        """
        格式化相对时间(如"3小时前")

        Args:
            dt: 日期时间
            locale: 语言区域
            user_timezone: 用户时区

        Returns:
            相对时间字符串
        """
        # 转换到用户时区
        local_dt = self.convert_to_user_timezone(dt, user_timezone)
        now = datetime.now(ZoneInfo(user_timezone))

        diff = now - local_dt
        seconds = int(diff.total_seconds())

        # 相对时间文本
        relative_texts = {
            'zh-CN': {
                'just_now': '刚刚',
                'minute': '分钟前',
                'hour': '小时前',
                'day': '天前',
                'week': '周前',
                'month': '个月前',
                'year': '年前',
            },
            'en-US': {
                'just_now': 'just now',
                'minute': ' minute ago',
                'hour': ' hour ago',
                'day': ' day ago',
                'week': ' week ago',
                'month': ' month ago',
                'year': ' year ago',
            },
            'ja-JP': {
                'just_now': 'たった今',
                'minute': '分前',
                'hour': '時間前',
                'day': '日前',
                'week': '週間前',
                'month': 'ヶ月前',
                'year': '年前',
            },
        }

        texts = relative_texts.get(locale, relative_texts['en-US'])

        if seconds < 60:
            return texts['just_now']
        elif seconds < 3600:
            minutes = seconds // 60
            return f"{minutes}{texts['minute']}"
        elif seconds < 86400:
            hours = seconds // 3600
            return f"{hours}{texts['hour']}"
        elif seconds < 604800:
            days = seconds // 86400
            return f"{days}{texts['day']}"
        elif seconds < 2592000:
            weeks = seconds // 604800
            return f"{weeks}{texts['week']}"
        elif seconds < 31536000:
            months = seconds // 2592000
            return f"{months}{texts['month']}"
        else:
            years = seconds // 31536000
            return f"{years}{texts['year']}"

    def format_currency(self, amount: float, locale: str = 'en-US',
                        currency_code: str = None) -> str:
        """
        格式化货币

        Args:
            amount: 金额
            locale: 语言区域
            currency_code: 货币代码(可选)

        Returns:
            格式化后的货币字符串
        """
        if not currency_code:
            currency_code = self._currency_codes.get(locale, 'USD')

        symbol = self._currency_symbols.get(locale, '$')

        # 获取数字格式
        num_format = self._number_formats.get(locale, {'thousands': ',', 'decimal': '.'})

        # 格式化数字
        formatted_amount = self._format_number(amount, num_format)

        # 不同地区的货币符号位置
        if locale in ['en-US', 'en-GB', 'fr-FR', 'de-DE', 'es-ES', 'pt-BR']:
            return f"{symbol}{formatted_amount}"
        elif locale in ['zh-CN', 'ja-JP', 'ko-KR']:
            return f"{symbol}{formatted_amount}"
        else:
            return f"{formatted_amount} {symbol}"

    def _format_number(self, number: float, num_format: Dict) -> str:
        """
        格式化数字（千位分隔符和小数点）

        Args:
            number: 数字
            num_format: 数字格式配置

        Returns:
            格式化后的数字字符串
        """
        thousands_sep = num_format['thousands']
        decimal_sep = num_format['decimal']

        # 分离整数和小数部分
        if isinstance(number, int):
            integer_part = str(number)
            decimal_part = ''
        else:
            integer_part, decimal_part = f"{number:.2f}".split('.')
            decimal_part = decimal_sep + decimal_part

        # 添加千位分隔符
        reversed_int = integer_part[::-1]
        groups = [reversed_int[i:i + 3] for i in range(0, len(reversed_int), 3)]
        formatted_int = thousands_sep.join(groups)[::-1]

        return formatted_int + decimal_part

    def get_user_locale_info(self, locale: str = 'en-US') -> Dict:
        """
        获取用户区域完整信息

        Args:
            locale: 语言区域

        Returns:
            区域信息字典
        """
        timezone = self._timezone_map.get(locale, 'UTC')
        currency_symbol = self._currency_symbols.get(locale, '$')
        currency_code = self._currency_codes.get(locale, 'USD')
        date_format = self._date_formats.get(locale, '%Y-%m-%d')
        datetime_format = self._datetime_formats.get(locale, '%Y-%m-%d %H:%M:%S')
        number_format = self._number_formats.get(locale, {'thousands': ',', 'decimal': '.'})

        return {
            'locale': locale,
            'timezone': timezone,
            'currency': {
                'symbol': currency_symbol,
                'code': currency_code,
            },
            'formats': {
                'date': date_format,
                'datetime': datetime_format,
                'number': number_format,
            },
        }

    def get_supported_locales(self) -> List[str]:
        """
        获取支持的语言区域列表

        Returns:
            区域代码列表
        """
        return list(self._timezone_map.keys())

    def get_timezone_offset(self, timezone_name: str) -> str:
        """
        获取时区偏移量

        Args:
            timezone_name: 时区名称

        Returns:
            偏移量字符串(如 +08:00)
        """
        try:
            tz = ZoneInfo(timezone_name)
            now = datetime.now(tz)
            offset = now.utcoffset()

            total_seconds = int(offset.total_seconds())
            hours, remainder = divmod(abs(total_seconds), 3600)
            minutes = remainder // 60

            sign = '+' if total_seconds >= 0 else '-'
            return f"{sign}{hours:02d}:{minutes:02d}"
        except Exception as e:
            logger.error(f"Failed to get timezone offset: {str(e)}")
            return '+00:00'


# 全局实例
localization_service = LocalizationService()
