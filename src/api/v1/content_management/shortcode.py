"""
Shortcode短代码API
提供短代码解析和管理功能
"""

from fastapi import APIRouter
from pydantic import BaseModel

from shared.services.content_management.shortcode_service import shortcode_service
from src.api.v1.core.responses import ApiResponse

router = APIRouter(tags=["shortcode"])


class ShortcodeParseRequest(BaseModel):
    """短代码解析请求"""
    content: str


@router.post("/parse")
async def parse_shortcodes(request_data: ShortcodeParseRequest):
    """
    解析内容中的短代码
    
    Args:
        request_data: 包含内容的请求体
        
    Returns:
        解析后的内容
    """
    try:
        parsed_content = shortcode_service.parse(request_data.content)
        
        return ApiResponse(
            success=True,
            data={
                'original': request_data.content,
                'parsed': parsed_content
            }
        )
    except Exception as e:
        return ApiResponse(success=False, error=f"解析失败: {str(e)}")


@router.get("/list")
async def list_shortcodes():
    """
    获取所有已注册的短代码列表
    
    Returns:
        短代码名称列表
    """
    try:
        shortcodes = list(shortcode_service.shortcodes.keys())
        
        return ApiResponse(
            success=True,
            data={
                'shortcodes': shortcodes,
                'count': len(shortcodes)
            }
        )
    except Exception as e:
        return ApiResponse(success=False, error=f"获取失败: {str(e)}")


@router.get("/help/{name}")
async def get_shortcode_help(name: str):
    """
    获取短代码使用说明
    
    Args:
        name: 短代码名称
        
    Returns:
        使用说明
    """
    help_docs = {
        'gallery': {
            'description': '图片画廊',
            'usage': '[gallery ids="1,2,3" columns="3"]',
            'attributes': {
                'ids': '图片ID列表(逗号分隔)',
                'columns': '列数(默认3)'
            },
            'example': '[gallery ids="1,2,3,4" columns="2"]'
        },
        'embed': {
            'description': '嵌入视频或其他内容',
            'usage': '[embed url="https://youtube.com/watch?v=<video-id>"]',
            'attributes': {
                'url': '嵌入URL'
            },
            'example': '[embed]https://www.youtube.com/watch?v=dQw4w9WgXcQ[/embed]'
        },
        'button': {
            'description': '按钮',
            'usage': '[button url="#" style="primary"]Text[/button]',
            'attributes': {
                'url': '链接地址',
                'style': '样式(primary/secondary/success/danger/outline)',
                'target': '打开方式(_self/_blank)'
            },
            'example': '[button url="/contact" style="primary"]联系我们[/button]'
        },
        'columns': {
            'description': '分栏布局',
            'usage': '[columns count="2"][column]Content[/column][column]Content[/column][/columns]',
            'attributes': {
                'count': '列数'
            },
            'example': '''[columns count="2"]
[column span="1"]左侧内容[/column]
[column span="1"]右侧内容[/column]
[/columns]'''
        },
        'caption': {
            'description': '图片说明文字',
            'usage': '[caption align="center"]Caption text[/caption]',
            'attributes': {
                'align': '对齐方式(left/center/right)'
            },
            'example': '[caption align="center"]这是一张图片的说明[/caption]'
        }
    }
    
    if name in help_docs:
        return ApiResponse(
            success=True,
            data=help_docs[name]
        )
    else:
        return ApiResponse(
            success=False,
            error=f"未找到短代码 '{name}' 的说明"
        )
