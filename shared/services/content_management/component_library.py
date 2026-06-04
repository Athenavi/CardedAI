"""
预制页面组件库
提供常用的营销和展示组件，用于可视化页面构建器

包含组件：
- Hero Section (英雄横幅)
- Features Grid (特性网格)
- Testimonials (客户评价)
- CTA (行动号召)
- Pricing Table (价格表)
- FAQ (常见问题)
- Team Members (团队成员)
- Contact Form (联系表单)
"""
from typing import Dict, Any, List
from dataclasses import dataclass


@dataclass
class ComponentTemplate:
    """组件模板定义"""
    name: str  # 组件名称
    category: str  # 分类：marketing, content, layout, forms
    description: str  # 描述
    preview_html: str  # 预览 HTML
    default_data: Dict[str, Any]  # 默认数据
    customization_options: Dict[str, Any]  # 自定义选项


class ComponentLibrary:
    """预制组件库管理器"""

    def __init__(self):
        self.components: Dict[str, ComponentTemplate] = {}
        self._register_default_components()

    def _register_default_components(self):
        """注册默认组件"""

        # ═══════════ Marketing Components ═══════════

        self.register_component(ComponentTemplate(
            name="hero-section",
            category="marketing",
            description="大型标题横幅，适用于首页顶部",
            preview_html='''
<div class="hero-section bg-gradient-to-r from-blue-600 to-purple-600 text-white py-20 px-8">
    <div class="max-w-6xl mx-auto text-center">
        <h1 class="text-5xl font-bold mb-4">Welcome to FastBlog</h1>
        <p class="text-xl mb-8 opacity-90">The next-generation CMS powered by AI</p>
        <button class="bg-white text-blue-600 px-8 py-3 rounded-full font-semibold hover:bg-gray-100 transition">
            Get Started
        </button>
    </div>
</div>
            ''',
            default_data={
                "title": "Welcome to FastBlog",
                "subtitle": "The next-generation CMS powered by AI",
                "cta_text": "Get Started",
                "cta_link": "/signup",
                "background_type": "gradient",
                "background_color": "from-blue-600 to-purple-600",
                "alignment": "center"
            },
            customization_options={
                "title": {"type": "string", "label": "主标题"},
                "subtitle": {"type": "string", "label": "副标题"},
                "cta_text": {"type": "string", "label": "按钮文字"},
                "cta_link": {"type": "string", "label": "按钮链接"},
                "background_type": {
                    "type": "select",
                    "options": ["gradient", "solid", "image"],
                    "label": "背景类型"
                },
                "alignment": {
                    "type": "select",
                    "options": ["left", "center", "right"],
                    "label": "对齐方式"
                }
            }
        ))

        self.register_component(ComponentTemplate(
            name="features-grid",
            category="marketing",
            description="特性展示网格，突出产品优势",
            preview_html='''
<div class="features-grid py-16 px-8 bg-gray-50">
    <div class="max-w-6xl mx-auto">
        <h2 class="text-3xl font-bold text-center mb-12">Key Features</h2>
        <div class="grid grid-cols-1 md:grid-cols-3 gap-8">
            <div class="feature-card bg-white p-6 rounded-xl shadow-sm">
                <div class="w-12 h-12 bg-blue-100 rounded-lg flex items-center justify-center mb-4">
                    <span class="text-2xl">⚡</span>
                </div>
                <h3 class="text-xl font-semibold mb-2">Lightning Fast</h3>
                <p class="text-gray-600">Optimized for speed and performance</p>
            </div>
            <div class="feature-card bg-white p-6 rounded-xl shadow-sm">
                <div class="w-12 h-12 bg-green-100 rounded-lg flex items-center justify-center mb-4">
                    <span class="text-2xl">🤖</span>
                </div>
                <h3 class="text-xl font-semibold mb-2">AI Powered</h3>
                <p class="text-gray-600">Smart content generation and optimization</p>
            </div>
            <div class="feature-card bg-white p-6 rounded-xl shadow-sm">
                <div class="w-12 h-12 bg-purple-100 rounded-lg flex items-center justify-center mb-4">
                    <span class="text-2xl">🔒</span>
                </div>
                <h3 class="text-xl font-semibold mb-2">Secure</h3>
                <p class="text-gray-600">Enterprise-grade security built-in</p>
            </div>
        </div>
    </div>
</div>
            ''',
            default_data={
                "title": "Key Features",
                "features": [
                    {
                        "icon": "⚡",
                        "title": "Lightning Fast",
                        "description": "Optimized for speed and performance",
                        "icon_bg": "bg-blue-100"
                    },
                    {
                        "icon": "🤖",
                        "title": "AI Powered",
                        "description": "Smart content generation and optimization",
                        "icon_bg": "bg-green-100"
                    },
                    {
                        "icon": "🔒",
                        "title": "Secure",
                        "description": "Enterprise-grade security built-in",
                        "icon_bg": "bg-purple-100"
                    }
                ],
                "columns": 3,
                "background_color": "bg-gray-50"
            },
            customization_options={
                "title": {"type": "string", "label": "标题"},
                "features": {"type": "array", "label": "特性列表"},
                "columns": {
                    "type": "select",
                    "options": [1, 2, 3, 4],
                    "label": "列数"
                }
            }
        ))

        self.register_component(ComponentTemplate(
            name="cta-section",
            category="marketing",
            description="行动号召区域，促进用户转化",
            preview_html='''
<div class="cta-section bg-blue-600 text-white py-16 px-8">
    <div class="max-w-4xl mx-auto text-center">
        <h2 class="text-3xl font-bold mb-4">Ready to Get Started?</h2>
        <p class="text-xl mb-8 opacity-90">Join thousands of satisfied users today</p>
        <div class="flex gap-4 justify-center">
            <button class="bg-white text-blue-600 px-8 py-3 rounded-full font-semibold hover:bg-gray-100 transition">
                Start Free Trial
            </button>
            <button class="border-2 border-white px-8 py-3 rounded-full font-semibold hover:bg-white hover:text-blue-600 transition">
                Learn More
            </button>
        </div>
    </div>
</div>
            ''',
            default_data={
                "title": "Ready to Get Started?",
                "subtitle": "Join thousands of satisfied users today",
                "primary_button": {
                    "text": "Start Free Trial",
                    "link": "/signup",
                    "style": "filled"
                },
                "secondary_button": {
                    "text": "Learn More",
                    "link": "/about",
                    "style": "outline"
                },
                "background_color": "bg-blue-600"
            },
            customization_options={
                "title": {"type": "string", "label": "标题"},
                "subtitle": {"type": "string", "label": "副标题"},
                "primary_button": {"type": "object", "label": "主要按钮"},
                "secondary_button": {"type": "object", "label": "次要按钮"}
            }
        ))

        self.register_component(ComponentTemplate(
            name="testimonials",
            category="marketing",
            description="客户评价展示，增强信任度",
            preview_html='''
<div class="testimonials py-16 px-8 bg-white">
    <div class="max-w-6xl mx-auto">
        <h2 class="text-3xl font-bold text-center mb-12">What Our Users Say</h2>
        <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-8">
            <div class="testimonial-card bg-gray-50 p-6 rounded-xl">
                <div class="flex items-center mb-4">
                    <img src="/avatar/user1.jpg" alt="User" class="w-12 h-12 rounded-full mr-4">
                    <div>
                        <h4 class="font-semibold">John Doe</h4>
                        <p class="text-sm text-gray-600">CEO at Tech Corp</p>
                    </div>
                </div>
                <p class="text-gray-700">"FastBlog has transformed how we manage content. The AI features are incredible!"</p>
                <div class="flex mt-4 text-yellow-500">★★★★★</div>
            </div>
        </div>
    </div>
</div>
            ''',
            default_data={
                "title": "What Our Users Say",
                "testimonials": [
                    {
                        "name": "John Doe",
                        "role": "CEO at Tech Corp",
                        "avatar": "/avatar/user1.jpg",
                        "content": "FastBlog has transformed how we manage content. The AI features are incredible!",
                        "rating": 5
                    }
                ],
                "columns": 3
            },
            customization_options={
                "title": {"type": "string", "label": "标题"},
                "testimonials": {"type": "array", "label": "评价列表"},
                "columns": {
                    "type": "select",
                    "options": [1, 2, 3],
                    "label": "列数"
                }
            }
        ))

        self.register_component(ComponentTemplate(
            name="pricing-table",
            category="marketing",
            description="价格表展示，清晰呈现套餐方案",
            preview_html='''
<div class="pricing-table py-16 px-8 bg-gray-50">
    <div class="max-w-6xl mx-auto">
        <h2 class="text-3xl font-bold text-center mb-4">Choose Your Plan</h2>
        <p class="text-center text-gray-600 mb-12">Simple, transparent pricing for everyone</p>
        <div class="grid grid-cols-1 md:grid-cols-3 gap-8">
            <div class="pricing-card bg-white p-8 rounded-xl shadow-sm border-2 border-transparent hover:border-blue-600 transition">
                <h3 class="text-xl font-bold mb-2">Free</h3>
                <div class="text-4xl font-bold mb-4">$0<span class="text-lg text-gray-600">/mo</span></div>
                <ul class="space-y-3 mb-8">
                    <li class="flex items-center"><span class="text-green-500 mr-2">✓</span> 5 Articles</li>
                    <li class="flex items-center"><span class="text-green-500 mr-2">✓</span> Basic Analytics</li>
                </ul>
                <button class="w-full py-3 border-2 border-blue-600 text-blue-600 rounded-full font-semibold hover:bg-blue-600 hover:text-white transition">
                    Get Started
                </button>
            </div>
        </div>
    </div>
</div>
            ''',
            default_data={
                "title": "Choose Your Plan",
                "subtitle": "Simple, transparent pricing for everyone",
                "plans": [
                    {
                        "name": "Free",
                        "price": "$0",
                        "period": "/mo",
                        "features": ["5 Articles", "Basic Analytics"],
                        "button_text": "Get Started",
                        "button_style": "outline",
                        "highlighted": False
                    }
                ]
            },
            customization_options={
                "title": {"type": "string", "label": "标题"},
                "plans": {"type": "array", "label": "套餐列表"}
            }
        ))

        # ═══════════ Content Components ═══════════

        self.register_component(ComponentTemplate(
            name="faq-section",
            category="content",
            description="常见问题解答，可折叠展开",
            preview_html='''
<div class="faq-section py-16 px-8 bg-white">
    <div class="max-w-4xl mx-auto">
        <h2 class="text-3xl font-bold text-center mb-12">Frequently Asked Questions</h2>
        <div class="space-y-4">
            <details class="faq-item border rounded-lg p-6 cursor-pointer">
                <summary class="font-semibold text-lg">What is FastBlog?</summary>
                <p class="mt-4 text-gray-700">FastBlog is a next-generation CMS with AI-powered features...</p>
            </details>
        </div>
    </div>
</div>
            ''',
            default_data={
                "title": "Frequently Asked Questions",
                "faqs": [
                    {
                        "question": "What is FastBlog?",
                        "answer": "FastBlog is a next-generation CMS with AI-powered features..."
                    }
                ]
            },
            customization_options={
                "title": {"type": "string", "label": "标题"},
                "faqs": {"type": "array", "label": "问答列表"}
            }
        ))

        self.register_component(ComponentTemplate(
            name="team-members",
            category="content",
            description="团队成员展示",
            preview_html='''
<div class="team-section py-16 px-8 bg-gray-50">
    <div class="max-w-6xl mx-auto">
        <h2 class="text-3xl font-bold text-center mb-12">Meet Our Team</h2>
        <div class="grid grid-cols-1 md:grid-cols-4 gap-8">
            <div class="team-member text-center">
                <img src="/avatar/member1.jpg" alt="Member" class="w-32 h-32 rounded-full mx-auto mb-4">
                <h3 class="font-semibold text-lg">Jane Smith</h3>
                <p class="text-gray-600">Founder & CEO</p>
            </div>
        </div>
    </div>
</div>
            ''',
            default_data={
                "title": "Meet Our Team",
                "members": [
                    {
                        "name": "Jane Smith",
                        "role": "Founder & CEO",
                        "avatar": "/avatar/member1.jpg",
                        "social_links": {}
                    }
                ],
                "columns": 4
            },
            customization_options={
                "title": {"type": "string", "label": "标题"},
                "members": {"type": "array", "label": "成员列表"}
            }
        ))

        # ═══════════ Form Components ═══════════

        self.register_component(ComponentTemplate(
            name="contact-form",
            category="forms",
            description="联系表单，支持姓名、邮箱、消息",
            preview_html='''
<div class="contact-form py-16 px-8 bg-white">
    <div class="max-w-2xl mx-auto">
        <h2 class="text-3xl font-bold text-center mb-8">Get in Touch</h2>
        <form class="space-y-6">
            <div>
                <label class="block text-sm font-medium mb-2">Name</label>
                <input type="text" class="w-full px-4 py-2 border rounded-lg">
            </div>
            <div>
                <label class="block text-sm font-medium mb-2">Email</label>
                <input type="email" class="w-full px-4 py-2 border rounded-lg">
            </div>
            <div>
                <label class="block text-sm font-medium mb-2">Message</label>
                <textarea rows="4" class="w-full px-4 py-2 border rounded-lg"></textarea>
            </div>
            <button type="submit" class="w-full bg-blue-600 text-white py-3 rounded-lg font-semibold hover:bg-blue-700 transition">
                Send Message
            </button>
        </form>
    </div>
</div>
            ''',
            default_data={
                "title": "Get in Touch",
                "fields": [
                    {"type": "text", "label": "Name", "required": True},
                    {"type": "email", "label": "Email", "required": True},
                    {"type": "textarea", "label": "Message", "required": True}
                ],
                "submit_text": "Send Message",
                "success_message": "Thank you! We'll get back to you soon."
            },
            customization_options={
                "title": {"type": "string", "label": "标题"},
                "fields": {"type": "array", "label": "表单字段"},
                "submit_text": {"type": "string", "label": "提交按钮文字"}
            }
        ))

    def register_component(self, component: ComponentTemplate):
        """注册组件"""
        self.components[component.name] = component

    def get_component(self, name: str) -> ComponentTemplate:
        """获取组件模板"""
        if name not in self.components:
            raise ValueError(f"Component '{name}' not found")
        return self.components[name]

    def get_all_components(self) -> List[ComponentTemplate]:
        """获取所有组件"""
        return list(self.components.values())

    def get_components_by_category(self, category: str) -> List[ComponentTemplate]:
        """按分类获取组件"""
        return [c for c in self.components.values() if c.category == category]

    def render_component(self, name: str, data: Dict[str, Any] = None) -> str:
        """渲染组件为 HTML
        
        Args:
            name: 组件名称
            data: 自定义数据（覆盖默认值）
            
        Returns:
            渲染后的 HTML
        """
        component = self.get_component(name)

        # 合并默认数据和自定义数据
        if data:
            merged_data = {**component.default_data, **data}
        else:
            merged_data = component.default_data.copy()

        # 根据组件类型动态生成 HTML
        if name == "hero-section":
            return self._render_hero(merged_data)
        elif name == "features-grid":
            return self._render_features_grid(merged_data)
        elif name == "cta-section":
            return self._render_cta(merged_data)
        elif name == "testimonials":
            return self._render_testimonials(merged_data)
        elif name == "pricing-table":
            return self._render_pricing(merged_data)
        elif name == "faq-section":
            return self._render_faq(merged_data)
        elif name == "team-members":
            return self._render_team(merged_data)
        elif name == "contact-form":
            return self._render_contact_form(merged_data)
        else:
            return component.preview_html

    def _render_hero(self, data: Dict[str, Any]) -> str:
        """渲染 Hero 组件"""
        alignment_class = {
            "left": "text-left",
            "center": "text-center",
            "right": "text-right"
        }.get(data.get("alignment", "center"), "text-center")

        bg_class = data.get("background_color", "from-blue-600 to-purple-600")

        return f'''
<div class="hero-section bg-gradient-to-r {bg_class} text-white py-20 px-8">
    <div class="max-w-6xl mx-auto {alignment_class}">
        <h1 class="text-5xl font-bold mb-4">{data.get("title", "")}</h1>
        <p class="text-xl mb-8 opacity-90">{data.get("subtitle", "")}</p>
        <button class="bg-white text-blue-600 px-8 py-3 rounded-full font-semibold hover:bg-gray-100 transition">
            {data.get("cta_text", "Get Started")}
        </button>
    </div>
</div>
        '''

    def _render_features_grid(self, data: Dict[str, Any]) -> str:
        """渲染特性网格组件"""
        columns = data.get("columns", 3)
        features = data.get("features", [])

        features_html = ""
        for feature in features:
            features_html += f'''
<div class="feature-card bg-white p-6 rounded-xl shadow-sm">
    <div class="w-12 h-12 {feature.get('icon_bg', 'bg-blue-100')} rounded-lg flex items-center justify-center mb-4">
        <span class="text-2xl">{feature.get('icon', '⭐')}</span>
    </div>
    <h3 class="text-xl font-semibold mb-2">{feature.get('title', '')}</h3>
    <p class="text-gray-600">{feature.get('description', '')}</p>
</div>
            '''

        return f'''
<div class="features-grid py-16 px-8 bg-gray-50">
    <div class="max-w-6xl mx-auto">
        <h2 class="text-3xl font-bold text-center mb-12">{data.get('title', '')}</h2>
        <div class="grid grid-cols-1 md:grid-cols-{columns} gap-8">
            {features_html}
        </div>
    </div>
</div>
        '''

    def _render_cta(self, data: Dict[str, Any]) -> str:
        """渲染 CTA 组件"""
        primary_btn = data.get("primary_button", {})
        secondary_btn = data.get("secondary_button", {})

        primary_html = ""
        if primary_btn:
            primary_html = f'''
<button class="bg-white text-blue-600 px-8 py-3 rounded-full font-semibold hover:bg-gray-100 transition">
    {primary_btn.get('text', 'Get Started')}
</button>
            '''

        secondary_html = ""
        if secondary_btn:
            secondary_html = f'''
<button class="border-2 border-white px-8 py-3 rounded-full font-semibold hover:bg-white hover:text-blue-600 transition">
    {secondary_btn.get('text', 'Learn More')}
</button>
            '''

        return f'''
<div class="cta-section bg-blue-600 text-white py-16 px-8">
    <div class="max-w-4xl mx-auto text-center">
        <h2 class="text-3xl font-bold mb-4">{data.get('title', '')}</h2>
        <p class="text-xl mb-8 opacity-90">{data.get('subtitle', '')}</p>
        <div class="flex gap-4 justify-center">
            {primary_html}
            {secondary_html}
        </div>
    </div>
</div>
        '''

    def _render_testimonials(self, data: Dict[str, Any]) -> str:
        """渲染评价组件"""
        columns = data.get("columns", 3)
        testimonials = data.get("testimonials", [])

        testimonials_html = ""
        for t in testimonials:
            stars = "★" * t.get("rating", 5)
            testimonials_html += f'''
<div class="testimonial-card bg-gray-50 p-6 rounded-xl">
    <div class="flex items-center mb-4">
        <img src="{t.get('avatar', '/avatar/default.jpg')}" alt="{t.get('name', '')}" class="w-12 h-12 rounded-full mr-4">
        <div>
            <h4 class="font-semibold">{t.get('name', '')}</h4>
            <p class="text-sm text-gray-600">{t.get('role', '')}</p>
        </div>
    </div>
    <p class="text-gray-700">"{t.get('content', '')}"</p>
    <div class="flex mt-4 text-yellow-500">{stars}</div>
</div>
            '''

        return f'''
<div class="testimonials py-16 px-8 bg-white">
    <div class="max-w-6xl mx-auto">
        <h2 class="text-3xl font-bold text-center mb-12">{data.get('title', '')}</h2>
        <div class="grid grid-cols-1 md:grid-cols-{columns} gap-8">
            {testimonials_html}
        </div>
    </div>
</div>
        '''

    def _render_pricing(self, data: Dict[str, Any]) -> str:
        """渲染价格表组件"""
        plans = data.get("plans", [])

        plans_html = ""
        for plan in plans:
            highlighted_class = "border-blue-600 transform scale-105" if plan.get(
                "highlighted") else "border-transparent"
            button_class = "bg-blue-600 text-white hover:bg-blue-700" if plan.get(
                "button_style") == "filled" else "border-2 border-blue-600 text-blue-600 hover:bg-blue-600 hover:text-white"

            features_html = "".join(
                [f'<li class="flex items-center"><span class="text-green-500 mr-2">✓</span>{f}</li>' for f in
                 plan.get("features", [])])

            plans_html += f'''
<div class="pricing-card bg-white p-8 rounded-xl shadow-sm border-2 {highlighted_class} transition">
    <h3 class="text-xl font-bold mb-2">{plan.get('name', '')}</h3>
    <div class="text-4xl font-bold mb-4">{plan.get('price', '$0')}<span class="text-lg text-gray-600">{plan.get('period', '/mo')}</span></div>
    <ul class="space-y-3 mb-8">
        {features_html}
    </ul>
    <button class="w-full py-3 {button_class} rounded-full font-semibold transition">
        {plan.get('button_text', 'Get Started')}
    </button>
</div>
            '''

        return f'''
<div class="pricing-table py-16 px-8 bg-gray-50">
    <div class="max-w-6xl mx-auto">
        <h2 class="text-3xl font-bold text-center mb-4">{data.get('title', '')}</h2>
        <p class="text-center text-gray-600 mb-12">{data.get('subtitle', '')}</p>
        <div class="grid grid-cols-1 md:grid-cols-3 gap-8">
            {plans_html}
        </div>
    </div>
</div>
        '''

    def _render_faq(self, data: Dict[str, Any]) -> str:
        """渲染 FAQ 组件"""
        faqs = data.get("faqs", [])

        faqs_html = ""
        for faq in faqs:
            faqs_html += f'''
<details class="faq-item border rounded-lg p-6 cursor-pointer">
    <summary class="font-semibold text-lg">{faq.get('question', '')}</summary>
    <p class="mt-4 text-gray-700">{faq.get('answer', '')}</p>
</details>
            '''

        return f'''
<div class="faq-section py-16 px-8 bg-white">
    <div class="max-w-4xl mx-auto">
        <h2 class="text-3xl font-bold text-center mb-12">{data.get('title', '')}</h2>
        <div class="space-y-4">
            {faqs_html}
        </div>
    </div>
</div>
        '''

    def _render_team(self, data: Dict[str, Any]) -> str:
        """渲染团队组件"""
        columns = data.get("columns", 4)
        members = data.get("members", [])

        members_html = ""
        for member in members:
            members_html += f'''
<div class="team-member text-center">
    <img src="{member.get('avatar', '/avatar/default.jpg')}" alt="{member.get('name', '')}" class="w-32 h-32 rounded-full mx-auto mb-4">
    <h3 class="font-semibold text-lg">{member.get('name', '')}</h3>
    <p class="text-gray-600">{member.get('role', '')}</p>
</div>
            '''

        return f'''
<div class="team-section py-16 px-8 bg-gray-50">
    <div class="max-w-6xl mx-auto">
        <h2 class="text-3xl font-bold text-center mb-12">{data.get('title', '')}</h2>
        <div class="grid grid-cols-1 md:grid-cols-{columns} gap-8">
            {members_html}
        </div>
    </div>
</div>
        '''

    def _render_contact_form(self, data: Dict[str, Any]) -> str:
        """渲染联系表单组件"""
        fields = data.get("fields", [])

        fields_html = ""
        for field in fields:
            field_type = field.get("type", "text")
            required = 'required' if field.get("required") else ""

            if field_type == "textarea":
                fields_html += f'''
<div>
    <label class="block text-sm font-medium mb-2">{field.get('label', '')}</label>
    <textarea rows="4" class="w-full px-4 py-2 border rounded-lg" {required}></textarea>
</div>
                '''
            else:
                fields_html += f'''
<div>
    <label class="block text-sm font-medium mb-2">{field.get('label', '')}</label>
    <input type="{field_type}" class="w-full px-4 py-2 border rounded-lg" {required}>
</div>
                '''

        return f'''
<div class="contact-form py-16 px-8 bg-white">
    <div class="max-w-2xl mx-auto">
        <h2 class="text-3xl font-bold text-center mb-8">{data.get('title', '')}</h2>
        <form class="space-y-6">
            {fields_html}
            <button type="submit" class="w-full bg-blue-600 text-white py-3 rounded-lg font-semibold hover:bg-blue-700 transition">
                {data.get('submit_text', 'Send Message')}
            </button>
        </form>
    </div>
</div>
        '''


# 全局组件库实例
component_library = ComponentLibrary()
