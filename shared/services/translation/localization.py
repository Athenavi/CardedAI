"""
区域化设置服务

功能：
1. 日期格式本地化
2. 数字格式本地化
3. 货币格式本地化
4. 时区转换
"""
from datetime import datetime, timezone
from typing import Optional, Dict


class LocalizationService:
    """
    区域化设置服务
    
    参考 Intl API 和 moment.js 的设计模式
    """

    def __init__(self):
        # 区域化配置
        self.locale_configs = {
            'zh-CN': {
                'date_format': '%Y年%m月%d日',
                'datetime_format': '%Y年%m月%d日 %H:%M:%S',
                'time_format': '%H:%M:%S',
                'decimal_separator': '.',
                'thousands_separator': ',',
                'currency_symbol': '¥',
                'currency_position': 'before',  # before or after
                'first_day_of_week': 1,  # Monday
                'timezone': 'Asia/Shanghai',
            },
            'en': {
                'date_format': '%m/%d/%Y',
                'datetime_format': '%m/%d/%Y %I:%M %p',
                'time_format': '%I:%M %p',
                'decimal_separator': '.',
                'thousands_separator': ',',
                'currency_symbol': '$',
                'currency_position': 'before',
                'first_day_of_week': 0,  # Sunday
                'timezone': 'America/New_York',
            },
            'ar': {
                'date_format': '%Y/%m/%d',
                'datetime_format': '%Y/%m/%d %H:%M',
                'time_format': '%H:%M',
                'decimal_separator': '٫',
                'thousands_separator': '٬',
                'currency_symbol': 'ر.س',
                'currency_position': 'after',
                'first_day_of_week': 6,  # Saturday
                'timezone': 'Asia/Riyadh',
            },
            'he': {
                'date_format': '%d.%m.%Y',
                'datetime_format': '%d.%m.%Y %H:%M',
                'time_format': '%H:%M',
                'decimal_separator': '.',
                'thousands_separator': ',',
                'currency_symbol': '₪',
                'currency_position': 'after',
                'first_day_of_week': 0,  # Sunday
                'timezone': 'Asia/Jerusalem',
            },
            'ja': {
                'date_format': '%Y年%m月%d日',
                'datetime_format': '%Y年%m月%d日 %H時%M分',
                'time_format': '%H時%M分',
                'decimal_separator': '.',
                'thousands_separator': ',',
                'currency_symbol': '¥',
                'currency_position': 'before',
                'first_day_of_week': 0,  # Sunday
                'timezone': 'Asia/Tokyo',
            },
            'ko': {
                'date_format': '%Y년 %m월 %d일',
                'datetime_format': '%Y년 %m월 %d일 %H시 %M분',
                'time_format': '%H시 %M분',
                'decimal_separator': '.',
                'thousands_separator': ',',
                'currency_symbol': '₩',
                'currency_position': 'after',
                'first_day_of_week': 0,  # Sunday
                'timezone': 'Asia/Seoul',
            },
            'fr': {
                'date_format': '%d/%m/%Y',
                'datetime_format': '%d/%m/%Y %H:%M',
                'time_format': '%H:%M',
                'decimal_separator': ',',
                'thousands_separator': ' ',
                'currency_symbol': '€',
                'currency_position': 'after',
                'first_day_of_week': 1,  # Monday
                'timezone': 'Europe/Paris',
            },
            'de': {
                'date_format': '%d.%m.%Y',
                'datetime_format': '%d.%m.%Y %H:%M',
                'time_format': '%H:%M',
                'decimal_separator': ',',
                'thousands_separator': '.',
                'currency_symbol': '€',
                'currency_position': 'after',
                'first_day_of_week': 1,  # Monday
                'timezone': 'Europe/Berlin',
            },
            'es': {
                'date_format': '%d/%m/%Y',
                'datetime_format': '%d/%m/%Y %H:%M',
                'time_format': '%H:%M',
                'decimal_separator': ',',
                'thousands_separator': '.',
                'currency_symbol': '€',
                'currency_position': 'after',
                'first_day_of_week': 1,  # Monday
                'timezone': 'Europe/Madrid',
            },
        }

    def format_date(
            self,
            date: datetime,
            locale: str = 'zh-CN',
            format_type: str = 'date'
    ) -> str:
        """
        格式化日期
        
        Args:
            date: 日期对象
            locale: 语言代码
            format_type: 格式类型 ('date', 'datetime', 'time')
            
        Returns:
            格式化后的日期字符串
        """
        config = self.locale_configs.get(locale, self.locale_configs['zh-CN'])

        if format_type == 'date':
            fmt = config['date_format']
        elif format_type == 'datetime':
            fmt = config['datetime_format']
        elif format_type == 'time':
            fmt = config['time_format']
        else:
            fmt = config['date_format']

        try:
            return date.strftime(fmt)
        except Exception:
            return date.isoformat()

    def format_number(
            self,
            number: float,
            locale: str = 'zh-CN',
            decimals: int = 2
    ) -> str:
        """
        格式化数字
        
        Args:
            number: 数字
            locale: 语言代码
            decimals: 小数位数
            
        Returns:
            格式化后的数字字符串
        """
        config = self.locale_configs.get(locale, self.locale_configs['zh-CN'])

        # 四舍五入
        rounded = round(number, decimals)

        # 分割整数和小数部分
        if decimals > 0:
            int_part = int(rounded)
            dec_part = abs(rounded - int_part)
            dec_str = f"{dec_part:.{decimals}f}"[1:]  # 去掉 "0"
        else:
            int_part = int(rounded)
            dec_str = ''

        # 格式化整数部分（添加千位分隔符）
        int_str = str(abs(int_part))
        groups = []

        while int_str:
            groups.append(int_str[-3:])
            int_str = int_str[:-3]

        formatted_int = config['thousands_separator'].join(reversed(groups))

        # 添加负号
        if int_part < 0:
            formatted_int = '-' + formatted_int

        # 组合结果
        result = formatted_int + dec_str

        return result

    def format_currency(
            self,
            amount: float,
            currency: str = 'CNY',
            locale: str = 'zh-CN'
    ) -> str:
        """
        格式化货币
        
        Args:
            amount: 金额
            currency: 货币代码 (CNY, USD, EUR, etc.)
            locale: 语言代码
            
        Returns:
            格式化后的货币字符串
        """
        config = self.locale_configs.get(locale, self.locale_configs['zh-CN'])

        # 获取货币符号
        currency_symbols = {
            'CNY': '¥',
            'USD': '$',
            'EUR': '€',
            'JPY': '¥',
            'KRW': '₩',
            'GBP': '£',
            'SAR': 'ر.س',
            'ILS': '₪',
        }

        symbol = currency_symbols.get(currency, config['currency_symbol'])

        # 格式化数字
        formatted_amount = self.format_number(amount, locale, 2)

        # 组合符号和金额
        if config['currency_position'] == 'before':
            return f"{symbol}{formatted_amount}"
        else:
            return f"{formatted_amount} {symbol}"

    def convert_timezone(
            self,
            dt: datetime,
            from_tz: str = 'UTC',
            to_tz: Optional[str] = None,
            locale: str = 'zh-CN'
    ) -> datetime:
        """
        时区转换
        
        Args:
            dt: 日期时间对象
            from_tz: 源时区
            to_tz: 目标时区（如果为 None，使用 locale 的默认时区）
            locale: 语言代码
            
        Returns:
            转换后的日期时间对象
        """
        config = self.locale_configs.get(locale, self.locale_configs['zh-CN'])

        if to_tz is None:
            to_tz = config['timezone']

        # 简单实现：实际应该使用 pytz 或 zoneinfo
        # 这里只做占位，实际需要完整的时区数据库
        try:
            # 假设输入是 UTC
            if from_tz == 'UTC':
                utc_dt = dt.replace(tzinfo=timezone.utc)

                # 简单的时区偏移（实际需要完整的时区数据库）
                tz_offsets = {
                    'Asia/Shanghai': 8,
                    'America/New_York': -5,
                    'Asia/Tokyo': 9,
                    'Asia/Seoul': 9,
                    'Europe/Paris': 1,
                    'Europe/Berlin': 1,
                    'Europe/Madrid': 1,
                    'Asia/Riyadh': 3,
                    'Asia/Jerusalem': 2,
                }

                offset_hours = tz_offsets.get(to_tz, 0)
                from datetime import timedelta
                converted_dt = utc_dt + timedelta(hours=offset_hours)

                return converted_dt.replace(tzinfo=None)
        except Exception:
            pass

        return dt

    def get_locale_config(self, locale: str) -> Dict:
        """
        获取区域化配置
        
        Args:
            locale: 语言代码
            
        Returns:
            配置字典
        """
        return self.locale_configs.get(locale, self.locale_configs['zh-CN'])

    def get_supported_locales(self) -> list:
        """
        获取支持的语言列表
        
        Returns:
            语言代码列表
        """
        return list(self.locale_configs.keys())


# 全局实例
localization_service = LocalizationService()
