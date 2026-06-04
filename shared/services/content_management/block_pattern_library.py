"""
块模式（Block Patterns）系统
提供预设计的区块组合模板

架构说明：
- BuiltinBlockPattern: 内置模式的轻量级数据类（内存中使用）
- ORM BlockPattern (shared.models.block_pattern): 用户自定义模式的持久化模型
- 两类分离设计：内置模式硬编码无需持久化，用户自定义模式通过 ORM 持久化到数据库
"""

from datetime import datetime, timezone
from typing import Dict, List, Any, Optional


class BuiltinBlockPattern:
    """内置块模式数据类（仅用于硬编码的内置模式，不涉及数据库持久化）"""

    def __init__(
        self,
        slug: str,
        title: str,
        description: str,
        category: str,
        blocks: List[Dict[str, Any]],
        preview_image: Optional[str] = None,
        tags: Optional[List[str]] = None
    ):
        self.slug = slug
        self.title = title
        self.description = description
        self.category = category
        self.blocks = blocks
        self.preview_image = preview_image
        self.tags = tags or []
        self.created_at = datetime.now(timezone.utc)


class BlockPatternLibrary:
    """
    块模式库管理器

    提供预设计的区块组合模板，用户可以快速插入到文章中
    """

    def __init__(self):
        # 内置块模式
        self.builtin_patterns = self._load_builtin_patterns()

    def _load_builtin_patterns(self) -> List[BuiltinBlockPattern]:
        """加载内置块模式"""
        return [
            # Hero 区域
            BuiltinBlockPattern(
                slug="hero-basic",
                title="基础 Hero 区域",
                description="带有标题、副标题和按钮的醒目 Hero 区域",
                category="hero",
                blocks=[
                    {
                        "type": "section",
                        "attrs": {
                            "className": "bg-gradient-to-r from-blue-600 to-purple-600 text-white py-20 px-6 rounded-lg"
                        },
                        "children": [
                            {
                                "type": "heading",
                                "attrs": {"level": 1, "className": "text-4xl font-bold mb-4"},
                                "content": "欢迎来到我们的网站"
                            },
                            {
                                "type": "paragraph",
                                "attrs": {"className": "text-xl mb-8 opacity-90"},
                                "content": "这是一个引人注目的副标题，描述您的核心价值主张"
                            },
                            {
                                "type": "button",
                                "attrs": {
                                    "className": "bg-white text-blue-600 px-8 py-3 rounded-full font-semibold hover:bg-gray-100 transition-colors",
                                    "url": "#"
                                },
                                "content": "开始探索"
                            }
                        ]
                    }
                ],
                tags=["hero", "banner", "cta"]
            ),

            BuiltinBlockPattern(
                slug="hero-with-image",
                title="带图片的 Hero",
                description="左侧文字、右侧图片的 Hero 布局",
                category="hero",
                blocks=[
                    {
                        "type": "section",
                        "attrs": {"className": "grid md:grid-cols-2 gap-8 items-center py-16"},
                        "children": [
                            {
                                "type": "column",
                                "children": [
                                    {
                                        "type": "heading",
                                        "attrs": {"level": 2, "className": "text-3xl font-bold mb-4"},
                                        "content": "创新解决方案"
                                    },
                                    {
                                        "type": "paragraph",
                                        "attrs": {"className": "text-gray-600 mb-6"},
                                        "content": "我们提供最先进的解决方案，帮助您实现业务目标"
                                    },
                                    {
                                        "type": "button-group",
                                        "attrs": {"className": "flex gap-4"},
                                        "children": [
                                            {
                                                "type": "button",
                                                "attrs": {"className": "bg-blue-600 text-white px-6 py-2 rounded hover:bg-blue-700"},
                                                "content": "了解更多"
                                            },
                                            {
                                                "type": "button",
                                                "attrs": {"className": "border border-blue-600 text-blue-600 px-6 py-2 rounded hover:bg-blue-50"},
                                                "content": "联系我们"
                                            }
                                        ]
                                    }
                                ]
                            },
                            {
                                "type": "image",
                                "attrs": {
                                    "src": "/placeholder.jpg",
                                    "alt": "Hero Image",
                                    "className": "rounded-lg shadow-lg"
                                }
                            }
                        ]
                    }
                ],
                tags=["hero", "image", "two-column"]
            ),

            # 特性列表
            BuiltinBlockPattern(
                slug="features-grid",
                title="特性网格",
                description="三列特性展示，带图标和描述",
                category="features",
                blocks=[
                    {
                        "type": "section",
                        "attrs": {"className": "py-16"},
                        "children": [
                            {
                                "type": "heading",
                                "attrs": {"level": 2, "className": "text-3xl font-bold text-center mb-12"},
                                "content": "核心特性"
                            },
                            {
                                "type": "grid",
                                "attrs": {"className": "grid md:grid-cols-3 gap-8"},
                                "children": [
                                    {
                                        "type": "card",
                                        "attrs": {"className": "p-6 bg-white rounded-lg shadow-md hover:shadow-lg transition-shadow"},
                                        "children": [
                                            {"type": "icon", "attrs": {"name": "rocket", "className": "w-12 h-12 text-blue-600 mb-4"}},
                                            {"type": "heading", "attrs": {"level": 3, "className": "text-xl font-semibold mb-2"}, "content": "快速部署"},
                                            {"type": "paragraph", "attrs": {"className": "text-gray-600"}, "content": "几分钟内即可完成部署，无需复杂配置"}
                                        ]
                                    },
                                    {
                                        "type": "card",
                                        "attrs": {"className": "p-6 bg-white rounded-lg shadow-md hover:shadow-lg transition-shadow"},
                                        "children": [
                                            {"type": "icon", "attrs": {"name": "shield", "className": "w-12 h-12 text-green-600 mb-4"}},
                                            {"type": "heading", "attrs": {"level": 3, "className": "text-xl font-semibold mb-2"}, "content": "安全可靠"},
                                            {"type": "paragraph", "attrs": {"className": "text-gray-600"}, "content": "企业级安全防护，保障数据安全"}
                                        ]
                                    },
                                    {
                                        "type": "card",
                                        "attrs": {"className": "p-6 bg-white rounded-lg shadow-md hover:shadow-lg transition-shadow"},
                                        "children": [
                                            {"type": "icon", "attrs": {"name": "chart", "className": "w-12 h-12 text-purple-600 mb-4"}},
                                            {"type": "heading", "attrs": {"level": 3, "className": "text-xl font-semibold mb-2"}, "content": "数据分析"},
                                            {"type": "paragraph", "attrs": {"className": "text-gray-600"}, "content": "强大的分析工具，洞察业务趋势"}
                                        ]
                                    }
                                ]
                            }
                        ]
                    }
                ],
                tags=["features", "grid", "cards"]
            ),

            # 团队介绍
            BuiltinBlockPattern(
                slug="team-members",
                title="团队成员",
                description="展示团队成员的卡片布局",
                category="team",
                blocks=[
                    {
                        "type": "section",
                        "attrs": {"className": "py-16 bg-gray-50"},
                        "children": [
                            {
                                "type": "heading",
                                "attrs": {"level": 2, "className": "text-3xl font-bold text-center mb-4"},
                                "content": "我们的团队"
                            },
                            {
                                "type": "paragraph",
                                "attrs": {"className": "text-center text-gray-600 mb-12 max-w-2xl mx-auto"},
                                "content": "由经验丰富的专业人士组成的优秀团队"
                            },
                            {
                                "type": "grid",
                                "attrs": {"className": "grid md:grid-cols-4 gap-6"},
                                "children": [
                                    {
                                        "type": "card",
                                        "attrs": {"className": "bg-white rounded-lg overflow-hidden shadow-md text-center p-6"},
                                        "children": [
                                            {"type": "avatar", "attrs": {"src": "/avatar1.jpg", "size": "xl", "className": "mx-auto mb-4"}},
                                            {"type": "heading", "attrs": {"level": 4, "className": "font-semibold"}, "content": "张三"},
                                            {"type": "paragraph", "attrs": {"className": "text-sm text-gray-600"}, "content": "CEO & 创始人"},
                                            {
                                                "type": "social-links",
                                                "attrs": {"className": "flex justify-center gap-3 mt-3"},
                                                "children": [
                                                    {"type": "icon", "attrs": {"name": "twitter", "className": "text-gray-400 hover:text-blue-500"}},
                                                    {"type": "icon", "attrs": {"name": "linkedin", "className": "text-gray-400 hover:text-blue-700"}}
                                                ]
                                            }
                                        ]
                                    }
                                ]
                            }
                        ]
                    }
                ],
                tags=["team", "members", "profiles"]
            ),

            # 价格表
            BuiltinBlockPattern(
                slug="pricing-table",
                title="价格表",
                description="三档价格方案对比",
                category="pricing",
                blocks=[
                    {
                        "type": "section",
                        "attrs": {"className": "py-16"},
                        "children": [
                            {
                                "type": "heading",
                                "attrs": {"level": 2, "className": "text-3xl font-bold text-center mb-4"},
                                "content": "选择适合您的方案"
                            },
                            {
                                "type": "grid",
                                "attrs": {"className": "grid md:grid-cols-3 gap-8 max-w-5xl mx-auto"},
                                "children": [
                                    {
                                        "type": "card",
                                        "attrs": {"className": "border-2 border-gray-200 rounded-lg p-8 hover:border-blue-500 transition-colors"},
                                        "children": [
                                            {"type": "heading", "attrs": {"level": 3, "className": "text-xl font-bold mb-2"}, "content": "基础版"},
                                            {"type": "price", "attrs": {"amount": "¥99", "period": "/月", "className": "text-4xl font-bold text-blue-600 mb-4"}},
                                            {
                                                "type": "list",
                                                "attrs": {"className": "space-y-3 mb-6"},
                                                "children": [
                                                    {"type": "list-item", "attrs": {"icon": "check"}, "content": "10GB 存储空间"},
                                                    {"type": "list-item", "attrs": {"icon": "check"}, "content": "基础支持"},
                                                    {"type": "list-item", "attrs": {"icon": "check"}, "content": "单个用户"}
                                                ]
                                            },
                                            {"type": "button", "attrs": {"className": "w-full bg-blue-600 text-white py-3 rounded-lg hover:bg-blue-700"}, "content": "选择方案"}
                                        ]
                                    },
                                    {
                                        "type": "card",
                                        "attrs": {"className": "border-2 border-blue-500 rounded-lg p-8 relative bg-blue-50"},
                                        "children": [
                                            {"type": "badge", "attrs": {"text": "最受欢迎", "className": "absolute -top-3 left-1/2 transform -translate-x-1/2 bg-blue-600 text-white px-3 py-1 rounded-full text-sm"}},
                                            {"type": "heading", "attrs": {"level": 3, "className": "text-xl font-bold mb-2"}, "content": "专业版"},
                                            {"type": "price", "attrs": {"amount": "¥299", "period": "/月", "className": "text-4xl font-bold text-blue-600 mb-4"}},
                                            {
                                                "type": "list",
                                                "attrs": {"className": "space-y-3 mb-6"},
                                                "children": [
                                                    {"type": "list-item", "attrs": {"icon": "check"}, "content": "100GB 存储空间"},
                                                    {"type": "list-item", "attrs": {"icon": "check"}, "content": "优先支持"},
                                                    {"type": "list-item", "attrs": {"icon": "check"}, "content": "10个用户"}
                                                ]
                                            },
                                            {"type": "button", "attrs": {"className": "w-full bg-blue-600 text-white py-3 rounded-lg hover:bg-blue-700"}, "content": "选择方案"}
                                        ]
                                    }
                                ]
                            }
                        ]
                    }
                ],
                tags=["pricing", "plans", "comparison"]
            ),

            # 联系方式
            BuiltinBlockPattern(
                slug="contact-form",
                title="联系表单",
                description="简洁的联系表单布局",
                category="contact",
                blocks=[
                    {
                        "type": "section",
                        "attrs": {"className": "py-16 bg-gray-50"},
                        "children": [
                            {
                                "type": "grid",
                                "attrs": {"className": "grid md:grid-cols-2 gap-12 max-w-5xl mx-auto"},
                                "children": [
                                    {
                                        "type": "column",
                                        "children": [
                                            {"type": "heading", "attrs": {"level": 2, "className": "text-3xl font-bold mb-4"}, "content": "联系我们"},
                                            {"type": "paragraph", "attrs": {"className": "text-gray-600 mb-6"}, "content": "有任何问题？欢迎随时与我们联系"},
                                            {
                                                "type": "info-list",
                                                "attrs": {"className": "space-y-4"},
                                                "children": [
                                                    {"type": "info-item", "attrs": {"icon": "mail"}, "content": "contact@example.com"},
                                                    {"type": "info-item", "attrs": {"icon": "phone"}, "content": "+86 123 4567 8900"},
                                                    {"type": "info-item", "attrs": {"icon": "location"}, "content": "北京市朝阳区xxx路xxx号"}
                                                ]
                                            }
                                        ]
                                    },
                                    {
                                        "type": "form",
                                        "attrs": {"className": "bg-white p-8 rounded-lg shadow-md"},
                                        "children": [
                                            {"type": "form-field", "attrs": {"label": "姓名", "type": "text", "required": True}},
                                            {"type": "form-field", "attrs": {"label": "邮箱", "type": "email", "required": True}},
                                            {"type": "form-field", "attrs": {"label": "主题", "type": "text"}},
                                            {"type": "form-field", "attrs": {"label": "消息", "type": "textarea", "rows": 4, "required": True}},
                                            {"type": "button", "attrs": {"className": "w-full bg-blue-600 text-white py-3 rounded-lg hover:bg-blue-700", "type": "submit"}, "content": "发送消息"}
                                        ]
                                    }
                                ]
                            }
                        ]
                    }
                ],
                tags=["contact", "form", "communication"]
            ),

            # CTA 行动号召
            BuiltinBlockPattern(
                slug="cta-banner",
                title="CTA 横幅",
                description="醒目的行动号召横幅",
                category="cta",
                blocks=[
                    {
                        "type": "section",
                        "attrs": {"className": "bg-gradient-to-r from-purple-600 to-pink-600 text-white py-16 px-6 rounded-lg"},
                        "children": [
                            {
                                "type": "container",
                                "attrs": {"className": "max-w-4xl mx-auto text-center"},
                                "children": [
                                    {"type": "heading", "attrs": {"level": 2, "className": "text-3xl font-bold mb-4"}, "content": "准备好开始了吗？"},
                                    {"type": "paragraph", "attrs": {"className": "text-xl mb-8 opacity-90"}, "content": "立即加入，开启您的成功之旅"},
                                    {
                                        "type": "button-group",
                                        "attrs": {"className": "flex justify-center gap-4"},
                                        "children": [
                                            {"type": "button", "attrs": {"className": "bg-white text-purple-600 px-8 py-3 rounded-full font-semibold hover:bg-gray-100"}, "content": "免费注册"},
                                            {"type": "button", "attrs": {"className": "border-2 border-white text-white px-8 py-3 rounded-full font-semibold hover:bg-white hover:text-purple-600"}, "content": "观看演示"}
                                        ]
                                    }
                                ]
                            }
                        ]
                    }
                ],
                tags=["cta", "banner", "conversion"]
            ),

            # testimonials 客户评价
            BuiltinBlockPattern(
                slug="testimonials",
                title="客户评价",
                description="展示客户反馈和评价",
                category="testimonials",
                blocks=[
                    {
                        "type": "section",
                        "attrs": {"className": "py-16"},
                        "children": [
                            {"type": "heading", "attrs": {"level": 2, "className": "text-3xl font-bold text-center mb-12"}, "content": "客户怎么说"},
                            {
                                "type": "grid",
                                "attrs": {"className": "grid md:grid-cols-2 gap-8"},
                                "children": [
                                    {
                                        "type": "card",
                                        "attrs": {"className": "bg-white p-6 rounded-lg shadow-md"},
                                        "children": [
                                            {"type": "quote", "attrs": {"className": "text-gray-700 italic mb-4"}, "content": "这个产品彻底改变了我们的工作方式，效率提升了200%！"},
                                            {
                                                "type": "author",
                                                "attrs": {"className": "flex items-center gap-3"},
                                                "children": [
                                                    {"type": "avatar", "attrs": {"src": "/user1.jpg", "size": "md"}},
                                                    {"type": "text", "attrs": {"className": "font-semibold"}, "content": "李四"},
                                                    {"type": "text", "attrs": {"className": "text-sm text-gray-600"}, "content": "某公司 CEO"}
                                                ]
                                            }
                                        ]
                                    }
                                ]
                            }
                        ]
                    }
                ],
                tags=["testimonials", "reviews", "feedback"]
            ),

            # FAQ 常见问题
            BuiltinBlockPattern(
                slug="faq-section",
                title="FAQ 常见问题",
                description="可折叠的常见问题列表",
                category="faq",
                blocks=[
                    {
                        "type": "section",
                        "attrs": {"className": "py-16 max-w-4xl mx-auto"},
                        "children": [
                            {"type": "heading", "attrs": {"level": 2, "className": "text-3xl font-bold text-center mb-12"}, "content": "常见问题"},
                            {
                                "type": "accordion",
                                "attrs": {"className": "space-y-4"},
                                "children": [
                                    {
                                        "type": "accordion-item",
                                        "attrs": {"title": "如何开始使用？"},
                                        "content": "只需注册账号，按照引导完成设置即可开始使用。整个过程不超过5分钟。"
                                    },
                                    {
                                        "type": "accordion-item",
                                        "attrs": {"title": "支持哪些支付方式？"},
                                        "content": "我们支持支付宝、微信支付、信用卡等多种支付方式。"
                                    },
                                    {
                                        "type": "accordion-item",
                                        "attrs": {"title": "有免费试用吗？"},
                                        "content": "是的，我们提供14天免费试用，无需信用卡。"
                                    }
                                ]
                            }
                        ]
                    }
                ],
                tags=["faq", "questions", "help"]
            ),

            # Newsletter 订阅
            BuiltinBlockPattern(
                slug="newsletter-signup",
                title="邮件订阅",
                description="简洁的邮件订阅表单",
                category="newsletter",
                blocks=[
                    {
                        "type": "section",
                        "attrs": {"className": "bg-blue-50 py-12 px-6 rounded-lg"},
                        "children": [
                            {
                                "type": "container",
                                "attrs": {"className": "max-w-2xl mx-auto text-center"},
                                "children": [
                                    {"type": "heading", "attrs": {"level": 3, "className": "text-2xl font-bold mb-2"}, "content": "订阅我们的通讯"},
                                    {"type": "paragraph", "attrs": {"className": "text-gray-600 mb-6"}, "content": "获取最新的产品更新、技巧和独家优惠"},
                                    {
                                        "type": "form-inline",
                                        "attrs": {"className": "flex gap-3"},
                                        "children": [
                                            {"type": "input", "attrs": {"type": "email", "placeholder": "输入您的邮箱", "className": "flex-1 px-4 py-3 rounded-lg border focus:outline-none focus:ring-2 focus:ring-blue-500"}},
                                            {"type": "button", "attrs": {"className": "bg-blue-600 text-white px-6 py-3 rounded-lg hover:bg-blue-700 whitespace-nowrap"}, "content": "订阅"}
                                        ]
                                    },
                                    {"type": "text", "attrs": {"className": "text-sm text-gray-500 mt-3"}, "content": "我们尊重您的隐私，绝不发送垃圾邮件"}
                                ]
                            }
                        ]
                    }
                ],
                tags=["newsletter", "subscription", "email"]
            ),

            # Stats 统计数据
            BuiltinBlockPattern(
                slug="stats-counter",
                title="统计数据",
                description="展示关键业务数据",
                category="stats",
                blocks=[
                    {
                        "type": "section",
                        "attrs": {"className": "py-16 bg-gray-900 text-white"},
                        "children": [
                            {
                                "type": "grid",
                                "attrs": {"className": "grid md:grid-cols-4 gap-8 text-center"},
                                "children": [
                                    {
                                        "type": "stat",
                                        "children": [
                                            {"type": "number", "attrs": {"value": "10000+", "className": "text-4xl font-bold text-blue-400"}},
                                            {"type": "label", "attrs": {"className": "text-gray-400 mt-2"}, "content": "活跃用户"}
                                        ]
                                    },
                                    {
                                        "type": "stat",
                                        "children": [
                                            {"type": "number", "attrs": {"value": "500+", "className": "text-4xl font-bold text-green-400"}},
                                            {"type": "label", "attrs": {"className": "text-gray-400 mt-2"}, "content": "完成项目"}
                                        ]
                                    },
                                    {
                                        "type": "stat",
                                        "children": [
                                            {"type": "number", "attrs": {"value": "99%", "className": "text-4xl font-bold text-purple-400"}},
                                            {"type": "label", "attrs": {"className": "text-gray-400 mt-2"}, "content": "客户满意度"}
                                        ]
                                    },
                                    {
                                        "type": "stat",
                                        "children": [
                                            {"type": "number", "attrs": {"value": "24/7", "className": "text-4xl font-bold text-yellow-400"}},
                                            {"type": "label", "attrs": {"className": "text-gray-400 mt-2"}, "content": "技术支持"}
                                        ]
                                    }
                                ]
                            }
                        ]
                    }
                ],
                tags=["stats", "numbers", "metrics"]
            )
        ]

    def get_all_patterns(self, category: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        获取所有块模式

        Args:
            category: 可选的分类过滤

        Returns:
            块模式列表
        """
        patterns = self.builtin_patterns

        if category:
            patterns = [p for p in patterns if p.category == category]

        return [self._pattern_to_dict(p) for p in patterns]

    def get_pattern_by_slug(self, slug: str) -> Optional[Dict[str, Any]]:
        """
        根据 slug 获取块模式

        Args:
            slug: 模式标识

        Returns:
            块模式字典，不存在返回 None
        """
        for pattern in self.builtin_patterns:
            if pattern.slug == slug:
                return self._pattern_to_dict(pattern)
        return None

    def get_categories(self) -> List[str]:
        """获取所有分类"""
        categories = set(p.category for p in self.builtin_patterns)
        return sorted(list(categories))

    def search_patterns(self, query: str) -> List[Dict[str, Any]]:
        """
        搜索块模式

        Args:
            query: 搜索关键词

        Returns:
            匹配的块模式列表
        """
        query_lower = query.lower()
        results = []

        for pattern in self.builtin_patterns:
            if (query_lower in pattern.title.lower() or
                query_lower in pattern.description.lower() or
                any(query_lower in tag.lower() for tag in pattern.tags)):
                results.append(self._pattern_to_dict(pattern))

        return results

    def _pattern_to_dict(self, pattern: BuiltinBlockPattern) -> Dict[str, Any]:
        """将 BuiltinBlockPattern 对象转换为字典"""
        return {
            "slug": pattern.slug,
            "title": pattern.title,
            "description": pattern.description,
            "category": pattern.category,
            "blocks": pattern.blocks,
            "preview_image": pattern.preview_image,
            "tags": pattern.tags,
            "created_at": pattern.created_at.isoformat()
        }


# 全局实例
block_pattern_library = BlockPatternLibrary()
