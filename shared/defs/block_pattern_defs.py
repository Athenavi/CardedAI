"""
BlockPattern 模型的自定义方法定义
这些方法会被自动注入到生成的 SQLAlchemy BlockPattern 模型中
"""


def get_blocks_data(self):
    """
    获取解析后的块数据
    
    Returns:
        List[Dict]: 解析后的块数据列表
    """
    import json

    if not self.blocks:
        return []
    
    try:
        # 如果 blocks 是字符串，尝试解析 JSON
        if isinstance(self.blocks, str):
            return json.loads(self.blocks)
        # 如果已经是列表或字典，直接返回
        elif isinstance(self.blocks, (list, dict)):
            return self.blocks if isinstance(self.blocks, list) else [self.blocks]
        else:
            return []
    except (json.JSONDecodeError, TypeError):
        return []


def set_blocks_data(self, blocks_data) -> None:
    """
    设置块数据（自动序列化为 JSON）
    
    Args:
        blocks_data: 块数据列表
    """
    import json

    try:
        self.blocks = json.dumps(blocks_data, ensure_ascii=False)
    except (TypeError, ValueError):
        self.blocks = str(blocks_data)


def get_keywords_list(self):
    """
    获取关键词列表
    
    Returns:
        List[str]: 关键词列表
    """

    if not self.keywords:
        return []
    
    try:
        # 如果 keywords 是逗号分隔的字符串
        if isinstance(self.keywords, str):
            return [kw.strip() for kw in self.keywords.split(',') if kw.strip()]
        # 如果已经是列表
        elif isinstance(self.keywords, list):
            return self.keywords
        else:
            return []
    except Exception:
        return []


def set_keywords_list(self, keywords) -> None:
    """
    设置关键词列表（自动转换为逗号分隔的字符串）
    
    Args:
        keywords: 关键词列表
    """

    if isinstance(keywords, list):
        self.keywords = ','.join(keywords)
    elif isinstance(keywords, str):
        self.keywords = keywords


def is_custom_pattern(self) -> bool:
    """
    判断是否为自定义模式（非系统预定义）
    
    Returns:
        bool: 是否为自定义模式
    """
    return self.category == 'custom'


def to_pattern_dict(self):
    """
    转换为前端可用的模式字典格式
    
    Returns:
        Dict: 模式字典
    """

    return {
        'name': self.name,
        'title': self.title,
        'description': self.description,
        'category': self.category,
        'blocks': self.get_blocks_data(),
        'keywords': self.get_keywords_list(),
        'thumbnail': self.thumbnail,
        'viewport_width': self.viewport_width,
        'is_public': self.is_public,
        'created_at': self.created_at.isoformat() if self.created_at else None,
        'updated_at': self.updated_at.isoformat() if self.updated_at else None,
    }
