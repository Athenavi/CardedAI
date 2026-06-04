"""
SVG 清理和验证工具
用于安全地处理 SVG 文件，防止 XSS 攻击
"""
import re
from xml.etree import ElementTree as ET

# 允许的 SVG 标签
ALLOWED_SVG_TAGS = {
    'svg', 'g', 'path', 'circle', 'rect', 'ellipse', 'line', 'polyline', 'polygon',
    'text', 'tspan', 'textPath', 'defs', 'clipPath', 'mask', 'pattern', 'symbol',
    'use', 'image', 'foreignObject', 'desc', 'title', 'metadata',
    'linearGradient', 'radialGradient', 'stop', 'filter', 'feGaussianBlur',
    'feOffset', 'feBlend', 'feColorMatrix', 'feComponentTransfer',
    'feComposite', 'feConvolveMatrix', 'feDiffuseLighting',
    'feDisplacementMap', 'feFlood', 'feMerge', 'feMorphology',
    'feSpecularLighting', 'feTile', 'feTurbulence', 'feDistantLight',
    'fePointLight', 'feSpotLight', 'animate', 'animateTransform',
    'animateMotion', 'mpath', 'set', 'view', 'style'
}

# 允许的 SVG 属性
ALLOWED_SVG_ATTRS = {
    # 通用属性
    'id', 'class', 'style', 'transform', 'fill', 'stroke', 'stroke-width',
    'opacity', 'fill-opacity', 'stroke-opacity', 'clip-path', 'mask',
    'filter', 'x', 'y', 'width', 'height', 'viewBox', 'preserveAspectRatio',
    'xmlns', 'version',
    
    # 形状属性
    'cx', 'cy', 'r', 'rx', 'ry', 'x1', 'y1', 'x2', 'y2', 'points', 'd',
    
    # 文本属性
    'font-family', 'font-size', 'font-weight', 'text-anchor', 'dx', 'dy',
    'rotate', 'textLength', 'lengthAdjust',
    
    # 渐变属性
    'offset', 'stop-color', 'stop-opacity',
    
    # 图像属性
    'href', 'xlink:href',
    
    # 动画属性
    'attributeName', 'from', 'to', 'dur', 'repeatCount', 'begin',
    
    # 其他
    'display', 'visibility', 'overflow'
}

# 危险的标签（必须移除）
DANGEROUS_TAGS = {
    'script', 'style', 'foreignobject',  # foreignObject 可能包含 HTML
}

# 危险的属性（必须移除）
DANGEROUS_ATTR_PATTERNS = [
    re.compile(r'^on\w+$', re.IGNORECASE),  # onclick, onerror 等事件处理器
    re.compile(r'^javascript:', re.IGNORECASE),  # javascript: URL
    re.compile(r'^data:', re.IGNORECASE),  # data: URL (可能被滥用)
    re.compile(r'^vbscript:', re.IGNORECASE),  # vbscript: URL
]


def sanitize_svg(svg_content: str) -> str:
    """
    清理 SVG 内容，移除潜在的危险元素和属性
    
    Args:
        svg_content: 原始 SVG 内容
        
    Returns:
        清理后的 SVG 内容
        
    Raises:
        ValueError: 如果 SVG 格式无效或包含无法清理的危险内容
    """
    if not svg_content or not svg_content.strip():
        raise ValueError("SVG 内容为空")
    
    # 检查文件大小（限制为 1MB）
    if len(svg_content.encode('utf-8')) > 1024 * 1024:
        raise ValueError("SVG 文件大小超过限制 (1MB)")
    
    try:
        # 尝试解析 XML
        root = ET.fromstring(svg_content.encode('utf-8'))
    except ET.ParseError as e:
        raise ValueError(f"SVG 格式无效: {str(e)}")
    
    # 递归清理元素
    _clean_element(root)
    
    # 序列化回字符串
    cleaned_svg = ET.tostring(root, encoding='unicode', xml_declaration=False)
    
    # 添加 XML 声明
    if not cleaned_svg.startswith('<?xml'):
        cleaned_svg = '<?xml version="1.0" encoding="UTF-8"?>\n' + cleaned_svg
    
    return cleaned_svg


def _clean_element(element: ET.Element):
    """
    递归清理 SVG 元素及其子元素
    
    Args:
        element: 要清理的 XML 元素
    """
    tag = element.tag.lower()
    
    # 移除命名空间前缀
    if '}' in tag:
        tag = tag.split('}', 1)[1]
    
    # 检查是否是危险标签
    if tag in DANGEROUS_TAGS:
        # 直接移除整个元素及其子元素
        parent = element.getparent() if hasattr(element, 'getparent') else None
        if parent is not None:
            parent.remove(element)
        return
    
    # 检查是否是允许的标签
    if tag not in ALLOWED_SVG_TAGS and tag != 'svg':
        # 如果不是允许的标签，移除但保留子元素
        parent = element.getparent() if hasattr(element, 'getparent') else None
        if parent is not None:
            for child in list(element):
                parent.insert(list(parent).index(element), child)
            parent.remove(element)
        return
    
    # 清理属性
    attrs_to_remove = []
    for attr_name, attr_value in element.attrib.items():
        # 移除命名空间前缀
        clean_attr_name = attr_name
        if '}' in clean_attr_name:
            clean_attr_name = clean_attr_name.split('}', 1)[1]
        
        # 检查是否是危险属性
        is_dangerous = False
        
        # 检查属性名是否匹配危险模式
        for pattern in DANGEROUS_ATTR_PATTERNS:
            if pattern.match(clean_attr_name):
                is_dangerous = True
                break
        
        # 检查属性值是否包含危险内容
        if not is_dangerous:
            value_lower = attr_value.lower().strip()
            if any(pattern.match(value_lower) for pattern in DANGEROUS_ATTR_PATTERNS):
                is_dangerous = True
        
        # 检查是否在允许的属性列表中
        if not is_dangerous and clean_attr_name not in ALLOWED_SVG_ATTRS:
            # 允许一些常见的自定义属性（以 data- 开头）
            if not clean_attr_name.startswith('data-'):
                is_dangerous = True
        
        if is_dangerous:
            attrs_to_remove.append(attr_name)
    
    # 移除危险属性
    for attr_name in attrs_to_remove:
        del element.attrib[attr_name]
    
    # 递归清理子元素
    for child in list(element):
        _clean_element(child)


def validate_svg(svg_content: str) -> dict:
    """
    验证 SVG 文件并提取元数据
    
    Args:
        svg_content: SVG 内容
        
    Returns:
        包含 SVG 元数据的字典
    """
    try:
        root = ET.fromstring(svg_content.encode('utf-8'))
    except ET.ParseError as e:
        raise ValueError(f"SVG 格式无效: {str(e)}")
    
    # 提取基本信息
    metadata = {
        'width': root.get('width'),
        'height': root.get('height'),
        'viewBox': root.get('viewBox'),
    }
    
    # 解析 viewBox
    if metadata['viewBox']:
        try:
            parts = metadata['viewBox'].split()
            if len(parts) == 4:
                metadata['viewBox_parsed'] = {
                    'x': float(parts[0]),
                    'y': float(parts[1]),
                    'width': float(parts[2]),
                    'height': float(parts[3])
                }
        except (ValueError, IndexError):
            pass
    
    # 统计元素数量
    element_count = {}
    for elem in root.iter():
        tag = elem.tag
        if '}' in tag:
            tag = tag.split('}', 1)[1]
        element_count[tag] = element_count.get(tag, 0) + 1
    
    metadata['element_count'] = element_count
    metadata['total_elements'] = sum(element_count.values())
    
    return metadata


def optimize_svg(svg_content: str) -> str:
    """
    优化 SVG 文件（基础版本）
    
    Args:
        svg_content: SVG 内容
        
    Returns:
        优化后的 SVG 内容
    """
    try:
        root = ET.fromstring(svg_content.encode('utf-8'))
    except ET.ParseError:
        return svg_content
    
    # 移除注释（ElementTree 不保留注释，所以不需要特别处理）
    
    # 移除不必要的空白
    def remove_whitespace(elem):
        """递归移除文本节点中的多余空白"""
        if elem.text:
            elem.text = elem.text.strip()
        if elem.tail:
            elem.tail = elem.tail.strip()
        for child in elem:
            remove_whitespace(child)
    
    remove_whitespace(root)
    
    # 序列化（不带缩进以减小文件大小）
    optimized = ET.tostring(root, encoding='unicode', xml_declaration=False)
    
    # 添加 XML 声明
    if not optimized.startswith('<?xml'):
        optimized = '<?xml version="1.0" encoding="UTF-8"?>' + optimized
    
    return optimized
