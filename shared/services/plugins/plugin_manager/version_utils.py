"""
版本比较工具模块

提供统一的版本比较功能，避免在多个地方重复实现
"""


def compare_versions(v1: str, v2: str) -> int:
    """
    比较两个版本号
    
    Args:
        v1: 版本号1
        v2: 版本号2
        
    Returns:
        -1: v1 < v2
         0: v1 == v2
         1: v1 > v2
    """

    def normalize(v):
        """将版本号字符串转换为整数列表"""
        try:
            return [int(x) for x in v.split('.')]
        except (ValueError, AttributeError):
            return [0]

    v1_parts = normalize(v1)
    v2_parts = normalize(v2)

    # 补齐长度
    max_len = max(len(v1_parts), len(v2_parts))
    v1_parts.extend([0] * (max_len - len(v1_parts)))
    v2_parts.extend([0] * (max_len - len(v2_parts)))

    for a, b in zip(v1_parts, v2_parts):
        if a < b:
            return -1
        elif a > b:
            return 1

    return 0


def check_version_match(installed_version: str, required_version: str) -> bool:
    """
    检查版本是否匹配要求
    
    Args:
        installed_version: 已安装的版本
        required_version: 要求的版本（支持 >=, >, <=, <, =, ~, ^ 等前缀）
        
    Returns:
        是否匹配
    """
    # 处理不同的版本要求格式
    if required_version.startswith('>='):
        required = required_version[2:]
        return compare_versions(installed_version, required) >= 0
    elif required_version.startswith('>'):
        required = required_version[1:]
        return compare_versions(installed_version, required) > 0
    elif required_version.startswith('<='):
        required = required_version[2:]
        return compare_versions(installed_version, required) <= 0
    elif required_version.startswith('<'):
        required = required_version[1:]
        return compare_versions(installed_version, required) < 0
    elif required_version.startswith('=') or required_version.startswith('=='):
        required = required_version.lstrip('=')
        return compare_versions(installed_version, required) == 0
    elif required_version.startswith('~'):
        # 兼容版本：~1.2.3 表示 >=1.2.3 且 <1.3.0
        required = required_version[1:]
        parts = required.split('.')
        if len(parts) >= 2:
            upper_bound = f"{parts[0]}.{int(parts[1]) + 1}.0"
            return (compare_versions(installed_version, required) >= 0 and
                    compare_versions(installed_version, upper_bound) < 0)
        return compare_versions(installed_version, required) >= 0
    elif required_version.startswith('^'):
        # caret 版本：^1.2.3 表示 >=1.2.3 且 <2.0.0
        required = required_version[1:]
        parts = required.split('.')
        if len(parts) >= 1:
            upper_bound = f"{int(parts[0]) + 1}.0.0"
            return (compare_versions(installed_version, required) >= 0 and
                    compare_versions(installed_version, upper_bound) < 0)
        return compare_versions(installed_version, required) >= 0
    else:
        # 默认精确匹配
        return compare_versions(installed_version, required_version) == 0
