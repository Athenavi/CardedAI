"""
核心 Blocks 实现

提供丰富的内容块类型，包括基础块、高级块和业务块

功能:
1. 基础 Blocks（标题、段落、图片、视频、引用、代码、列表）
2. 高级 Blocks（图库、表格、嵌入、按钮、分隔线、间距）
3. 业务 Blocks（商品卡片、VIP内容、广告横幅、联系表单、社交分享）
"""

from shared.services.block_editor.core import (
    Block,
    BlockType,
    BlockSchema,
    BlockCategory,
    block_registry,
)


# ==================== 基础 Blocks ====================

def register_basic_blocks():
    """注册基础 Blocks"""

    # 视频块
    video_schema = BlockSchema(
        block_type=BlockType.VIDEO,
        name="Video",
        description="视频块，支持多种格式",
        category=BlockCategory.MEDIA,
        attributes={
            "src": {"type": "str", "required": True},
            "poster": {"type": "str", "required": False},
            "autoplay": {"type": "bool", "required": False, "default": False},
            "controls": {"type": "bool", "required": False, "default": True},
        },
        icon="video",
    )
    block_registry.register_block_type(video_schema)

    # 图库块
    gallery_schema = BlockSchema(
        block_type=BlockType.GALLERY,
        name="Gallery",
        description="图片图库",
        category=BlockCategory.MEDIA,
        attributes={
            "images": {"type": "list", "required": True},
            "columns": {"type": "int", "required": False, "default": 3},
            "link_to": {"type": "str", "required": False},
        },
        icon="gallery",
    )
    block_registry.register_block_type(gallery_schema)

    # 表格块
    table_schema = BlockSchema(
        block_type=BlockType.TABLE,
        name="Table",
        description="数据表格",
        category=BlockCategory.BASIC,
        attributes={
            "headers": {"type": "list", "required": False},
            "rows": {"type": "list", "required": True},
            "striped": {"type": "bool", "required": False, "default": True},
        },
        icon="table",
    )
    block_registry.register_block_type(table_schema)

    # 嵌入块
    embed_schema = BlockSchema(
        block_type=BlockType.EMBED,
        name="Embed",
        description="嵌入外部内容（YouTube、Twitter等）",
        category=BlockCategory.EMBEDS,
        attributes={
            "url": {"type": "str", "required": True},
            "provider": {"type": "str", "required": False},
            "width": {"type": "int", "required": False},
            "height": {"type": "int", "required": False},
        },
        icon="embed",
    )
    block_registry.register_block_type(embed_schema)

    # 按钮块
    button_schema = BlockSchema(
        block_type=BlockType.BUTTON,
        name="Button",
        description="可点击的按钮",
        category=BlockCategory.DESIGN,
        attributes={
            "text": {"type": "str", "required": True},
            "url": {"type": "str", "required": True},
            "style": {"type": "str", "required": False, "default": "primary"},
            "size": {"type": "str", "required": False, "default": "medium"},
        },
        icon="button",
    )
    block_registry.register_block_type(button_schema)


# ==================== 业务 Blocks ====================

def register_business_blocks():
    """注册业务 Blocks"""

    # 商品卡片
    product_card_schema = BlockSchema(
        block_type=BlockType.CUSTOM,
        name="Product Card",
        description="商品展示卡片",
        category=BlockCategory.WIDGETS,
        attributes={
            "product_id": {"type": "str", "required": True},
            "title": {"type": "str", "required": True},
            "price": {"type": "str", "required": True},
            "image": {"type": "str", "required": False},
            "description": {"type": "str", "required": False},
            "buy_url": {"type": "str", "required": False},
        },
        icon="shopping-cart",
    )
    block_registry.register_block_type(product_card_schema)

    # VIP 内容块
    vip_content_schema = BlockSchema(
        block_type=BlockType.CUSTOM,
        name="VIP Content",
        description="VIP 专属内容",
        category=BlockCategory.WIDGETS,
        attributes={
            "content": {"type": "str", "required": True},
            "min_level": {"type": "int", "required": False, "default": 1},
            "message": {"type": "str", "required": False},
        },
        icon="crown",
    )
    block_registry.register_block_type(vip_content_schema)

    # 广告横幅
    ad_banner_schema = BlockSchema(
        block_type=BlockType.CUSTOM,
        name="Ad Banner",
        description="广告横幅",
        category=BlockCategory.WIDGETS,
        attributes={
            "image": {"type": "str", "required": True},
            "link_url": {"type": "str", "required": True},
            "alt_text": {"type": "str", "required": False},
            "position": {"type": "str", "required": False, "default": "center"},
        },
        icon="advertising",
    )
    block_registry.register_block_type(ad_banner_schema)

    # 联系表单
    contact_form_schema = BlockSchema(
        block_type=BlockType.CUSTOM,
        name="Contact Form",
        description="联系表单",
        category=BlockCategory.WIDGETS,
        attributes={
            "fields": {"type": "list", "required": True},
            "submit_text": {"type": "str", "required": False, "default": "发送"},
            "success_message": {"type": "str", "required": False},
        },
        icon="mail",
    )
    block_registry.register_block_type(contact_form_schema)

    # 社交分享
    social_share_schema = BlockSchema(
        block_type=BlockType.CUSTOM,
        name="Social Share",
        description="社交分享按钮",
        category=BlockCategory.WIDGETS,
        attributes={
            "platforms": {"type": "list", "required": False, "default": ["wechat", "weibo", "twitter"]},
            "title": {"type": "str", "required": False},
            "url": {"type": "str", "required": False},
        },
        icon="share",
    )
    block_registry.register_block_type(social_share_schema)


# ==================== 自定义渲染器 ====================

def render_video_block(block: Block) -> str:
    """渲染视频块"""
    attrs = block.attributes
    src = attrs.get("src", "")
    poster = attrs.get("poster", "")
    autoplay = 'autoplay' if attrs.get("autoplay") else ''
    controls = 'controls' if attrs.get("controls", True) else ''

    html = f'<video src="{src}" poster="{poster}" {autoplay} {controls}>'
    html += '</video>'
    return html


def render_gallery_block(block: Block) -> str:
    """渲染图库块"""
    attrs = block.attributes
    images = attrs.get("images", [])
    columns = attrs.get("columns", 3)

    html = f'<div class="gallery" style="grid-template-columns: repeat({columns}, 1fr);">'
    for img in images:
        if isinstance(img, dict):
            src = img.get("src", "")
            alt = img.get("alt", "")
            html += f'<figure><img src="{src}" alt="{alt}" /></figure>'
        else:
            html += f'<figure><img src="{img}" alt="" /></figure>'
    html += '</div>'
    return html


def render_table_block(block: Block) -> str:
    """渲染表格块"""
    attrs = block.attributes
    headers = attrs.get("headers", [])
    rows = attrs.get("rows", [])
    striped = 'table-striped' if attrs.get("striped", True) else ''

    html = f'<table class="{striped}">'

    if headers:
        html += '<thead><tr>'
        for header in headers:
            html += f'<th>{header}</th>'
        html += '</tr></thead>'

    html += '<tbody>'
    for row in rows:
        html += '<tr>'
        for cell in row:
            html += f'<td>{cell}</td>'
        html += '</tr>'
    html += '</tbody></table>'

    return html


def render_embed_block(block: Block) -> str:
    """渲染嵌入块"""
    attrs = block.attributes
    url = attrs.get("url", "")
    provider = attrs.get("provider", "")
    width = attrs.get("width", 560)
    height = attrs.get("height", 315)

    # 根据不同提供商生成不同的嵌入代码
    if "youtube.com" in url or "youtu.be" in url:
        video_id = url.split("v=")[-1] if "v=" in url else url.split("/")[-1]
        return f'<iframe width="{width}" height="{height}" src="https://www.youtube.com/embed/{video_id}" frameborder="0" allowfullscreen></iframe>'

    elif "twitter.com" in url:
        return f'<blockquote class="twitter-tweet"><a href="{url}"></a></blockquote>'

    else:
        return f'<iframe src="{url}" width="{width}" height="{height}" frameborder="0"></iframe>'


def render_button_block(block: Block) -> str:
    """渲染按钮块"""
    attrs = block.attributes
    text = attrs.get("text", "")
    url = attrs.get("url", "")
    style = attrs.get("style", "primary")
    size = attrs.get("size", "medium")

    return f'<a href="{url}" class="btn btn-{style} btn-{size}">{text}</a>'


def render_product_card(block: Block) -> str:
    """渲染商品卡片"""
    attrs = block.attributes
    title = attrs.get("title", "")
    price = attrs.get("price", "")
    image = attrs.get("image", "")
    description = attrs.get("description", "")
    buy_url = attrs.get("buy_url", "")

    html = '<div class="product-card">'
    if image:
        html += f'<img src="{image}" alt="{title}" />'
    html += f'<h3>{title}</h3>'
    if description:
        html += f'<p>{description}</p>'
    html += f'<div class="price">{price}</div>'
    if buy_url:
        html += f'<a href="{buy_url}" class="btn">购买</a>'
    html += '</div>'

    return html


def render_vip_content(block: Block, user_level: int = 0) -> str:
    """
    渲染 VIP 内容

    Args:
        block: 块对象
        user_level: 当前用户等级，0 表示未登录用户

    Returns:
        渲染后的 HTML
    """
    attrs = block.attributes
    content = attrs.get("content", "")
    min_level = attrs.get("min_level", 1)
    message = attrs.get("message", "此内容为 VIP 专属")

    if user_level >= min_level:
        return f'''
<div class="vip-content" data-min-level="{min_level}">
    <div class="vip-badge">VIP</div>
    {content}
</div>
'''
    else:
        return f'''
<div class="vip-content vip-locked" data-min-level="{min_level}">
    <div class="vip-badge">VIP</div>
    <div class="vip-lock-overlay">
        <div class="vip-lock-icon">🔒</div>
        <p class="vip-lock-message">{message}</p>
        <p class="vip-lock-hint">需要 VIP 等级 ≥ {min_level}</p>
    </div>
</div>
'''


def render_ad_banner(block: Block) -> str:
    """渲染广告横幅"""
    attrs = block.attributes
    image = attrs.get("image", "")
    link_url = attrs.get("link_url", "")
    alt_text = attrs.get("alt_text", "Advertisement")

    return f'''
<div class="ad-banner">
    <a href="{link_url}" target="_blank" rel="nofollow">
        <img src="{image}" alt="{alt_text}" />
    </a>
</div>
'''


def render_contact_form(block: Block) -> str:
    """渲染联系表单"""
    attrs = block.attributes
    fields = attrs.get("fields", [])
    submit_text = attrs.get("submit_text", "发送")

    html = '<form class="contact-form">'
    for field in fields:
        field_type = field.get("type", "text")
        label = field.get("label", "")
        required = 'required' if field.get("required") else ''

        if field_type == "textarea":
            html += f'''
<div class="form-group">
    <label>{label}</label>
    <textarea name="{field.get('name', '')}" {required}></textarea>
</div>
'''
        else:
            html += f'''
<div class="form-group">
    <label>{label}</label>
    <input type="{field_type}" name="{field.get('name', '')}" {required} />
</div>
'''

    html += f'<button type="submit" class="btn">{submit_text}</button>'
    html += '</form>'

    return html


def render_social_share(block: Block) -> str:
    """渲染社交分享"""
    attrs = block.attributes
    platforms = attrs.get("platforms", ["wechat", "weibo", "twitter"])
    title = attrs.get("title", "")
    url = attrs.get("url", "")

    icons = {
        "wechat": "微信",
        "weibo": "微博",
        "twitter": "Twitter",
        "facebook": "Facebook",
        "linkedin": "LinkedIn",
    }

    html = '<div class="social-share">'
    for platform in platforms:
        icon = icons.get(platform, platform)
        html += f'<button class="share-btn share-{platform}">{icon}</button>'
    html += '</div>'

    return html


# ==================== 注册所有 Blocks 和渲染器 ====================

def register_all_blocks():
    """注册所有 Blocks"""
    # 注册基础 blocks
    register_basic_blocks()

    # 注册业务 blocks
    register_business_blocks()

    # 注册自定义渲染器
    block_registry.renderers["video"] = render_video_block
    block_registry.renderers["gallery"] = render_gallery_block
    block_registry.renderers["table"] = render_table_block
    block_registry.renderers["embed"] = render_embed_block
    block_registry.renderers["button"] = render_button_block

    # 注册业务 blocks 渲染器
    # 注意：这些使用 CUSTOM 类型，需要通过其他方式区分
    # 这里简化处理，实际应该为每个业务 block 创建独立的 BlockType


# 自动注册
register_all_blocks()
