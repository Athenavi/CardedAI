"""
安全工具模块
包含输入验证、SQL注入防护、XSS防护等功能
"""
import random
import re
import string
from urllib.parse import urlparse

from fastapi import Request
from sqlalchemy import text


def validate_input(input_string, allowed_pattern=None):
    """
    验证输入字符串的安全性
    
    :param input_string: 待验证的输入字符串
    :param allowed_pattern: 允许的正则模式
    :return: 验证结果和清理后的字符串
    """
    if input_string is None:
        return True, None

    # 检查是否有SQL注入尝试
    sql_patterns = [
        r"(?i)(union\s+select|select\s+\*|drop\s+\w+|create\s+\w+|alter\s+\w+|delete\s+from|insert\s+into)",
        r"(?i)(exec\s*\(|execute\s*\(|sp_|xp_)",
        r"(?i)(;|--|/\*|\*/|0x[0-9A-Fa-f]{2,})",
        r"(?i)(waitfor\s+delay|benchmark\(|sleep\(|pg_sleep\()",
    ]

    for pattern in sql_patterns:
        if re.search(pattern, input_string):
            return False, None

    # 如果提供了允许的模式，则验证是否符合
    if allowed_pattern and not re.match(allowed_pattern, input_string):
        return False, None

    # 清理输入
    cleaned_input = input_string.strip()
    return True, cleaned_input


def load_sensitive_words(file_path):
    try:
        with open(file_path, 'r', encoding='utf-8') as file:
            sensitive_words = set(word.strip().lower() for word in file)
        return sensitive_words
    except FileNotFoundError:
        return set()
    except IOError as e:
        print(e)
        return set()


def validate_xss(input_string):
    """
    验证输入字符串是否包含XSS尝试
    
    :param input_string: 待验证的输入字符串
    :return: 验证结果
    """
    if input_string is None:
        return True

    # XSS检测模式
    xss_patterns = [
        r"(?i)<script[^>]*>.*?</script>",  # 基本script标签
        r"(?i)<iframe[^>]*>.*?</iframe>",  # iframe标签
        r"(?i)<object[^>]*>.*?</object>",  # object标签
        r"(?i)<embed[^>]*>",  # embed标签
        r"(?i)<img[^>]*\s+on\w+\s*=",  # 图片标签中的事件处理器
        r"(?i)<[^>]*\s+on\w+\s*=",  # 任何标签中的事件处理器
        r"(?i)javascript\s*:",  # javascript: 协议
        r"(?i)vbscript\s*:",  # vbscript: 协议
        r"(?i)on\w+\s*=",  # 事件处理器属性
    ]

    for pattern in xss_patterns:
        if re.search(pattern, input_string):
            return False

    return True


def sanitize_sql_identifier(identifier):
    """
    清理SQL标识符（如表名、列名），防止SQL注入
    
    :param identifier: SQL标识符
    :return: 清理后的标识符
    """
    if not identifier:
        return identifier

    # 只允许字母、数字、下划线，且不能以数字开头
    if re.match(r'^[a-zA-Z_][a-zA-Z0-9_]*$', identifier) and len(identifier) <= 64:
        return identifier
    else:
        raise ValueError(f"Invalid SQL identifier: {identifier}")


def safe_query_builder(table_name, conditions=None, columns="*", order_by=None, limit=None):
    """
    安全的查询构建器，防止SQL注入
    
    :param table_name: 表名
    :param conditions: 条件字典，格式为 {'column': 'value'}
    :param columns: 要查询的列
    :param order_by: 排序字段
    :param limit: 限制返回记录数
    :return: SQLAlchemy TextClause 对象
    """
    # 验证表名
    sanitized_table = sanitize_sql_identifier(table_name)

    # 构建基础查询
    query_parts = [f"SELECT {columns} FROM {sanitized_table}"]

    # 处理条件
    if conditions and isinstance(conditions, dict):
        where_clauses = []
        for col, val in conditions.items():
            # 验证列名
            sanitized_col = sanitize_sql_identifier(col)
            where_clauses.append(f"{sanitized_col} = :{sanitized_col}")

        if where_clauses:
            query_parts.append("WHERE " + " AND ".join(where_clauses))

    # 处理排序
    if order_by:
        # 验证排序字段
        sanitized_order = sanitize_sql_identifier(order_by)
        query_parts.append(f"ORDER BY {sanitized_order}")

    # 处理限制
    if limit and isinstance(limit, int) and limit > 0:
        query_parts.append(f"LIMIT {limit}")

    query_str = " ".join(query_parts)
    return text(query_str)


def escape_html(text):
    """
    转义HTML特殊字符，防止XSS
    
    :param text: 待转义的文本
    :return: 转义后的文本
    """
    if text is None:
        return text

    return (str(text)
            .replace("&", "&amp;")
            .replace("<", "&lt;")
            .replace(">", "&gt;")
            .replace('"', "&quot;")
            .replace("'", "&#x27;"))


def validate_url(url_string, allowed_schemes=None):
    """
    验证URL的安全性
    
    :param url_string: URL字符串
    :param allowed_schemes: 允许的协议列表
    :return: 验证结果和标准化URL
    """
    if not url_string:
        return True, url_string

    if allowed_schemes is None:
        allowed_schemes = ['http', 'https', 'ftp']

    try:
        parsed = urlparse(url_string)
        if parsed.scheme not in allowed_schemes:
            return False, None
        return True, url_string
    except Exception:
        return False, None


def validate_password_strength(password):
    """
    验证密码强度
    """
    if len(password) < 8:
        return False, "密码长度至少8位"

    has_upper = any(c.isupper() for c in password)
    has_lower = any(c.islower() for c in password)
    has_digit = any(c.isdigit() for c in password)
    has_special = any(c in "!@#$%^&*()_+-=[]{}|;:,.<>?" for c in password)

    if not (has_upper and has_lower and has_digit and has_special):
        return False, "密码必须包含大写字母、小写字母、数字和特殊字符"

    return True, "密码强度符合要求"


def sanitize_filename(filename):
    """
    清理文件名，防止路径遍历攻击
    
    :param filename: 原始文件名
    :return: 清理后的文件名
    """
    if not filename:
        return filename

    # 移除路径分隔符以防止路径遍历
    filename = filename.replace('../', '').replace('..\\', '')
    filename = filename.replace('/', '').replace('\\', '')

    # 只允许字母、数字、下划线、连字符、点号
    sanitized = re.sub(r'[^\w.-]', '_', filename)

    return sanitized


def validate_integer(value, min_val=None, max_val=None):
    """
    验证整数值的安全性

    :param value: 待验证的值
    :param min_val: 最小值
    :param max_val: 最大值
    :return: 验证结果和整数值
    """
    try:
        int_val = int(value)
        if min_val is not None and int_val < min_val:
            return False, None
        if max_val is not None and int_val > max_val:
            return False, None
        return True, int_val
    except (ValueError, TypeError):
        return False, None


def validate_boolean(value):
    """
    验证布尔值

    :param value: 待验证的值
    :return: 验证结果和布尔值
    """
    if isinstance(value, bool):
        return True, value
    if isinstance(value, str):
        value = value.lower()
        if value in ['true', '1', 'yes', 'on']:
            return True, True
        elif value in ['false', '0', 'no', 'off']:
            return True, False
    elif isinstance(value, int):
        if value in [0, 1]:
            return True, bool(value)

    return False, None


def sql_injection_protection(*param_names):
    """
    SQL注入防护依赖函数，验证指定参数的安全性
    
    :param param_names: 需要验证的参数名称列表
    :return: 验证后的参数字典
    """
    from fastapi import HTTPException

    async def validate_params(
            request: Request
    ):
        validated_params = {}

        # 对于GET请求，检查查询参数
        for param_name in param_names:
            if param_name in request.query_params:
                value = request.query_params[param_name]
                is_valid, cleaned_value = validate_input(value)
                if not is_valid:
                    raise HTTPException(
                        status_code=400,
                        detail=f'Invalid input for parameter: {param_name}'
                    )
                validated_params[param_name] = cleaned_value

        # 对于POST/PUT请求，检查表单数据或JSON数据
        if request.method in ["POST", "PUT", "PATCH"]:
            try:
                # 尝试获取JSON数据
                json_data = await request.json()
                for param_name in param_names:
                    if param_name in json_data:
                        value = json_data[param_name]
                        is_valid, cleaned_value = validate_input(value)
                        if not is_valid:
                            raise HTTPException(
                                status_code=400,
                                detail=f'Invalid input for parameter: {param_name}'
                            )
                        validated_params[param_name] = cleaned_value
            except:
                # 如果不是JSON数据，检查表单数据
                try:
                    form_data = await request.form()
                    for param_name in param_names:
                        if param_name in form_data:
                            value = form_data[param_name]
                            is_valid, cleaned_value = validate_input(value)
                            if not is_valid:
                                raise HTTPException(
                                    status_code=400,
                                    detail=f'Invalid input for parameter: {param_name}'
                                )
                            validated_params[param_name] = cleaned_value
                except:
                    pass  # 如果既不是JSON也不是表单数据，跳过检查

        # 将验证后的参数附加到请求对象上，供后续处理使用
        if not hasattr(request.state, 'validated_params'):
            request.state.validated_params = {}
        request.state.validated_params.update(validated_params)

        # 返回验证后的参数字典
        return validated_params

    return validate_params


valid_language_codes = {
    'af', 'af-ZA', 'sq', 'sq-AL', 'ar', 'ar-DZ', 'ar-BH', 'ar-EG', 'ar-IQ',
    'ar-JO', 'ar-KW', 'ar-LB', 'ar-LY', 'ar-MA', 'ar-OM', 'ar-QA', 'ar-SA',
    'ar-SY', 'ar-TN', 'ar-AE', 'ar-YE', 'hy', 'hy-AM', 'az', 'az-AZ-Cyrl',
    'az-AZ-Latn', 'eu', 'eu-ES', 'be', 'be-BY', 'bg', 'bg-BG', 'ca', 'ca-ES',
    'zh-HK', 'zh-MO', 'zh-CN', 'zh-CHS', 'zh-SG', 'zh-TW', 'zh-CHT', 'hr',
    'hr-HR', 'cs', 'cs-CZ', 'da', 'da-DK', 'div', 'div-MV', 'nl', 'nl-BE',
    'nl-NL', 'en', 'en-AU', 'en-BZ', 'en-CA', 'en-CB', 'en-IE', 'en-JM',
    'en-NZ', 'en-PH', 'en-ZA', 'en-TT', 'en-GB', 'en-US', 'en-ZW', 'et',
    'et-EE', 'fo', 'fo-FO', 'fa', 'fa-IR', 'fi', 'fi-FI', 'fr', 'fr-BE',
    'fr-CA', 'fr-FR', 'fr-LU', 'fr-MC', 'fr-CH', 'gl', 'gl-ES', 'ka', 'ka-GE',
    'de', 'de-AT', 'de-DE', 'de-LI', 'de-LU', 'de-CH', 'el', 'el-GR', 'gu',
    'gu-IN', 'he', 'he-IL', 'hi', 'hi-IN', 'hu', 'hu-HU', 'is', 'is-IS',
    'id', 'id-ID', 'it', 'it-IT', 'it-CH', 'ja', 'ja-JP', 'kn', 'kn-IN',
    'kk', 'kk-KZ', 'kok', 'kok-IN', 'ko', 'ko-KR', 'ky', 'ky-KZ', 'lv',
    'lv-LV', 'lt', 'lt-LT', 'mk', 'mk-MK', 'ms', 'ms-BN', 'ms-MY', 'mr',
    'mr-IN', 'mn', 'mn-MN', 'no', 'nb-NO', 'nn-NO', 'pl', 'pl-PL', 'pt',
    'pt-BR', 'pt-PT', 'pa', 'pa-IN', 'ro', 'o-RO', 'ru', 'ru-RU', 'sa',
    'sa-IN', 'sr-SP-Cyrl', 'sr-SP-Latn', 'sk', 'sk-SK', 'sl', 'sl-SI', 'es',
    'es-AR', 'es-BO', 'es-CL', 'es-CO', 'es-CR', 'es-DO', 'es-EC', 'es-SV',
    'es-GT', 'es-HN', 'es-MX', 'es-NI', 'es-PA', 'es-PY', 'es-PE', 'es-PR',
    'es-ES', 'es-UY', 'es-VE', 'sw', 'sw-KE', 'sv', 'sv-FI', 'sv-SE', 'syr',
    'syr-SY', 'ta', 'ta-IN', 'tt', 'tt-RU', 'te', 'te-IN', 'th', 'th-TH',
    'tr', 'tr-TR', 'uk', 'uk-UA', 'ur', 'ur-PK', 'uz', 'uz-UZ-Cyrl',
    'uz-UZ-Latn', 'vi', 'vi-VN', 'zh-cn', 'zh-tw', 'zh-hk', 'en-hk', 'en-us',
    'en-gb', 'en-ww', 'en-ca', 'en-au', 'en-ie', 'en-fi', 'fi-fi', 'en-dk',
    'da-dk', 'en-il', 'he-il', 'en-za', 'en-in', 'en-no', 'en-sg', 'en-nz',
    'en-id', 'en-ph', 'en-th', 'en-my', 'en-xa', 'ko-kr', 'ja-jp', 'nl-nl',
    'nl-be', 'pt-pt', 'pt-br', 'fr-fr', 'fr-lu', 'fr-ch', 'fr-be', 'fr-ca',
    'es-la', 'es-es', 'es-ar', 'es-us', 'es-mx', 'es-co', 'es-pr', 'de-de',
    'de-at', 'de-ch', 'ru-ru', 'it-it', 'el-gr', 'no-no', 'hu-hu', 'tr-tr',
    'cs-cz', 'sl-sl', 'pl-pl', 'sv-se', 'es-cl'
}


# 检查代码是否在有效集合中

def is_valid_iso_language_code(iso_code: str) -> bool:
    """
    验证给定的ISO语言代码是否有效

    参数:
        iso_code (str): 要验证的语言代码(如zh-CN, en-US)

    返回:
        bool: 如果代码有效返回True，否则False
    """
    # 所有有效的语言代码集合(基于提供的对照表)

    return iso_code in valid_language_codes


def random_string(param):
    return ''.join(random.sample(string.ascii_letters + string.digits, param))


def validate_email_base(email):
    """验证邮箱格式"""
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return re.match(pattern, email) is not None


def is_valid_hash(length, f_hash):
    """
    验证哈希值是否为指定长度的十六进制字符串
    :param length: 哈希值的预期长度
    :param f_hash: 哈希值字符串
    :return: 如果哈希值有效则返回 True，否则返回 False
    """
    if f_hash is None or not isinstance(f_hash, str) or len(f_hash) != length or not all(
            c in '0123456789abcdef' for c in f_hash.lower()):
        return False
    return True
