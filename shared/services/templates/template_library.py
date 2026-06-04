"""
预制模板库

提供丰富的页面和文章模板，加速内容创作

功能:
1. 页面模板（落地页、关于页面、联系页面等）
2. 文章布局模板
3. 邮件模板
4. 模板分类和管理
5. 模板预览和自定义
"""

from datetime import datetime
from enum import Enum
from typing import Dict, Any, List, Optional


class TemplateCategory(Enum):
    """模板分类"""
    LANDING_PAGE = "landing_page"
    ABOUT_PAGE = "about_page"
    CONTACT_PAGE = "contact_page"
    ARTICLE_LAYOUT = "article_layout"
    EMAIL_TEMPLATE = "email_template"
    PRODUCT_PAGE = "product_page"
    PORTFOLIO = "portfolio"
    OTHER = "other"


class Template:
    """模板定义"""

    def __init__(
            self,
            template_id: str,
            name: str,
            description: str,
            category: TemplateCategory,
            preview_image: str = "",
            blocks_data: List[Dict[str, Any]] = None,
            html_content: str = "",
            metadata: Dict[str, Any] = None,
    ):
        self.template_id = template_id
        self.name = name
        self.description = description
        self.category = category
        self.preview_image = preview_image
        self.blocks_data = blocks_data or []
        self.html_content = html_content
        self.metadata = metadata or {}
        self.created_at = datetime.now().isoformat()
        self.updated_at = datetime.now().isoformat()

    def to_dict(self) -> Dict[str, Any]:
        return {
            "template_id": self.template_id,
            "name": self.name,
            "description": self.description,
            "category": self.category.value,
            "preview_image": self.preview_image,
            "blocks_data": self.blocks_data,
            "html_content": self.html_content,
            "metadata": self.metadata,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
        }


class TemplateLibrary:
    """
    模板库
    
    管理和提供预制模板
    """

    def __init__(self):
        self.templates: Dict[str, Template] = {}
        self._register_builtin_templates()

    def register_template(self, template: Template):
        """注册模板"""
        self.templates[template.template_id] = template

    def get_template(self, template_id: str) -> Optional[Template]:
        """获取模板"""
        return self.templates.get(template_id)

    def list_templates(
            self,
            category: TemplateCategory = None,
            search: str = None
    ) -> List[Dict[str, Any]]:
        """
        列出模板
        
        Args:
            category: 过滤分类
            search: 搜索关键词
            
        Returns:
            模板列表
        """
        templates_list = []

        for template in self.templates.values():
            # 分类过滤
            if category and template.category != category:
                continue

            # 搜索过滤
            if search:
                search_lower = search.lower()
                if (search_lower not in template.name.lower() and
                        search_lower not in template.description.lower()):
                    continue

            templates_list.append(template.to_dict())

        return templates_list

    def get_categories(self) -> Dict[str, int]:
        """获取分类统计"""
        stats = {}
        for template in self.templates.values():
            cat = template.category.value
            stats[cat] = stats.get(cat, 0) + 1
        return stats

    def _register_builtin_templates(self):
        """注册内置模板"""

        # ==================== 落地页模板 ====================
        landing_page = Template(
            template_id="landing-page-001",
            name="现代落地页",
            description="适合产品发布的现代化落地页模板",
            category=TemplateCategory.LANDING_PAGE,
            blocks_data=[
                {
                    "block_id": "hero-section",
                    "type": "heading",
                    "attributes": {
                        "content": "欢迎来到我们的产品",
                        "level": 1
                    }
                },
                {
                    "block_id": "hero-desc",
                    "type": "text",
                    "attributes": {
                        "content": "我们提供最优质的解决方案"
                    }
                },
                {
                    "block_id": "cta-button",
                    "type": "button",
                    "attributes": {
                        "text": "立即开始",
                        "url": "/signup",
                        "style": "primary"
                    }
                },
                {
                    "block_id": "features",
                    "type": "heading",
                    "attributes": {
                        "content": "核心功能",
                        "level": 2
                    }
                },
                {
                    "block_id": "feature-list",
                    "type": "list",
                    "attributes": {
                        "items": ["功能一", "功能二", "功能三"],
                        "ordered": False
                    }
                }
            ],
            metadata={
                "tags": ["landing", "modern", "product"],
                "popularity": 95
            }
        )
        self.register_template(landing_page)

        # ==================== 关于页面模板 ====================
        about_page = Template(
            template_id="about-page-001",
            name="公司简介",
            description="展示公司信息和团队的专业页面",
            category=TemplateCategory.ABOUT_PAGE,
            blocks_data=[
                {
                    "block_id": "about-title",
                    "type": "heading",
                    "attributes": {
                        "content": "关于我们",
                        "level": 1
                    }
                },
                {
                    "block_id": "about-intro",
                    "type": "text",
                    "attributes": {
                        "content": "我们是一家专注于创新的公司..."
                    }
                },
                {
                    "block_id": "mission",
                    "type": "quote",
                    "attributes": {
                        "content": "我们的使命是改变世界",
                        "cite": "CEO"
                    }
                },
                {
                    "block_id": "team-heading",
                    "type": "heading",
                    "attributes": {
                        "content": "核心团队",
                        "level": 2
                    }
                }
            ],
            metadata={
                "tags": ["about", "company", "team"],
                "popularity": 80
            }
        )
        self.register_template(about_page)

        # ==================== 联系页面模板 ====================
        contact_page = Template(
            template_id="contact-page-001",
            name="联系我们",
            description="包含联系表单和信息的页面",
            category=TemplateCategory.CONTACT_PAGE,
            blocks_data=[
                {
                    "block_id": "contact-title",
                    "type": "heading",
                    "attributes": {
                        "content": "联系我们",
                        "level": 1
                    }
                },
                {
                    "block_id": "contact-form",
                    "type": "custom",
                    "attributes": {
                        "fields": [
                            {"type": "text", "label": "姓名", "name": "name", "required": True},
                            {"type": "email", "label": "邮箱", "name": "email", "required": True},
                            {"type": "textarea", "label": "留言", "name": "message", "required": True}
                        ],
                        "submit_text": "发送消息"
                    }
                },
                {
                    "block_id": "contact-info",
                    "type": "text",
                    "attributes": {
                        "content": "邮箱: contact@example.com\n电话: 123-456-7890"
                    }
                }
            ],
            metadata={
                "tags": ["contact", "form"],
                "popularity": 85
            }
        )
        self.register_template(contact_page)

        # ==================== 文章布局模板 ====================
        article_standard = Template(
            template_id="article-standard-001",
            name="标准文章布局",
            description="适合博客文章的标准布局",
            category=TemplateCategory.ARTICLE_LAYOUT,
            blocks_data=[
                {
                    "block_id": "article-title",
                    "type": "heading",
                    "attributes": {
                        "content": "文章标题",
                        "level": 1
                    }
                },
                {
                    "block_id": "article-meta",
                    "type": "text",
                    "attributes": {
                        "content": "作者 | 日期 | 分类"
                    }
                },
                {
                    "block_id": "featured-image",
                    "type": "image",
                    "attributes": {
                        "src": "/images/placeholder.jpg",
                        "alt": "特色图片"
                    }
                },
                {
                    "block_id": "intro",
                    "type": "text",
                    "attributes": {
                        "content": "引言段落..."
                    }
                },
                {
                    "block_id": "section1",
                    "type": "heading",
                    "attributes": {
                        "content": "第一部分",
                        "level": 2
                    }
                },
                {
                    "block_id": "content1",
                    "type": "text",
                    "attributes": {
                        "content": "内容..."
                    }
                },
                {
                    "block_id": "conclusion",
                    "type": "heading",
                    "attributes": {
                        "content": "总结",
                        "level": 2
                    }
                }
            ],
            metadata={
                "tags": ["article", "blog", "standard"],
                "popularity": 90
            }
        )
        self.register_template(article_standard)

        # ==================== 邮件模板 ====================
        welcome_email = Template(
            template_id="email-welcome-001",
            name="欢迎邮件",
            description="新用户注册欢迎邮件模板",
            category=TemplateCategory.EMAIL_TEMPLATE,
            html_content="""
<!DOCTYPE html>
<html>
<head>
    <style>
        body { font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto; }
        .header { background: #3b82f6; color: white; padding: 20px; text-align: center; }
        .content { padding: 20px; }
        .button { display: inline-block; padding: 10px 20px; background: #3b82f6; color: white; text-decoration: none; border-radius: 5px; }
        .footer { padding: 20px; text-align: center; color: #666; font-size: 12px; }
    </style>
</head>
<body>
    <div class="header">
        <h1>欢迎加入！</h1>
    </div>
    <div class="content">
        <p>亲爱的用户，</p>
        <p>感谢您注册我们的服务。我们很高兴您成为我们社区的一员。</p>
        <p>点击下方按钮开始探索：</p>
        <p><a href="#" class="button">开始使用</a></p>
        <p>如果您有任何问题，请随时联系我们。</p>
    </div>
    <div class="footer">
        <p>此邮件由系统自动发送，请勿回复。</p>
    </div>
</body>
</html>
            """,
            metadata={
                "tags": ["email", "welcome", "onboarding"],
                "popularity": 88
            }
        )
        self.register_template(welcome_email)

        # ==================== 作品集模板 ====================
        portfolio_page = Template(
            template_id="portfolio-001",
            name="作品集展示",
            description="展示作品和项目的页面",
            category=TemplateCategory.PORTFOLIO,
            blocks_data=[
                {
                    "block_id": "portfolio-title",
                    "type": "heading",
                    "attributes": {
                        "content": "我的作品集",
                        "level": 1
                    }
                },
                {
                    "block_id": "gallery",
                    "type": "gallery",
                    "attributes": {
                        "images": [
                            {"src": "/images/project1.jpg", "alt": "项目1"},
                            {"src": "/images/project2.jpg", "alt": "项目2"},
                            {"src": "/images/project3.jpg", "alt": "项目3"}
                        ],
                        "columns": 3
                    }
                }
            ],
            metadata={
                "tags": ["portfolio", "gallery", "projects"],
                "popularity": 75
            }
        )
        self.register_template(portfolio_page)


# 全局实例
template_library = TemplateLibrary()
