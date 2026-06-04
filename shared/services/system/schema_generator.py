"""
Schema.org 结构化数据生成器
用于 SEO 优化，生成 JSON-LD 格式的结构化数据
"""

from datetime import datetime
from typing import Dict, Any, List, Optional


class SchemaGenerator:
    """
    Schema.org 结构化数据生成器
    
    支持的模式:
    - Article (文章)
    - BreadcrumbList (面包屑导航)
    - Organization (组织)
    - Person (人物)
    - WebSite (网站)
    - FAQPage (常见问题)
    - ImageObject (图片)
    - VideoObject (视频)
    """
    
    def __init__(self, base_url: str = ""):
        self.base_url = base_url.rstrip('/')
    
    def generate_article_schema(
        self,
        title: str,
        description: str,
        url: str,
        author_name: str,
        author_url: str = "",
        publish_date: Optional[str] = None,
        modified_date: Optional[str] = None,
        image_url: str = "",
        keywords: List[str] = None,
        category: str = ""
    ) -> Dict[str, Any]:
        """
        生成文章 Schema
        
        Args:
            title: 文章标题
            description: 文章描述
            url: 文章 URL
            author_name: 作者名称
            author_url: 作者主页 URL
            publish_date: 发布日期 (ISO 8601 格式)
            modified_date: 修改日期 (ISO 8601 格式)
            image_url: 特色图片 URL
            keywords: 关键词列表
            category: 分类
            
        Returns:
            JSON-LD 格式的字典
        """
        schema = {
            "@context": "https://schema.org",
            "@type": "Article",
            "headline": title,
            "description": description,
            "url": url,
            "author": {
                "@type": "Person",
                "name": author_name,
            },
            "publisher": {
                "@type": "Organization",
                "name": self._get_site_name(),
            },
            "datePublished": publish_date or datetime.now().isoformat(),
        }
        
        if author_url:
            schema["author"]["url"] = author_url
        
        if modified_date:
            schema["dateModified"] = modified_date
        
        if image_url:
            schema["image"] = {
                "@type": "ImageObject",
                "url": image_url,
            }
        
        if keywords:
            schema["keywords"] = ", ".join(keywords)
        
        if category:
            schema["articleSection"] = category
        
        return schema
    
    def generate_breadcrumb_schema(
        self,
        items: List[Dict[str, str]]
    ) -> Dict[str, Any]:
        """
        生成面包屑导航 Schema
        
        Args:
            items: 面包屑项列表，每项包含 'name' 和 'url'
            
        Returns:
            JSON-LD 格式的字典
        """
        item_list = []
        for index, item in enumerate(items, 1):
            item_list.append({
                "@type": "ListItem",
                "position": index,
                "name": item['name'],
                "item": item['url']
            })
        
        return {
            "@context": "https://schema.org",
            "@type": "BreadcrumbList",
            "itemListElement": item_list
        }
    
    def generate_organization_schema(
        self,
        name: str,
        url: str,
        logo_url: str = "",
        description: str = "",
        social_profiles: Dict[str, str] = None,
        contact_email: str = "",
        phone: str = ""
    ) -> Dict[str, Any]:
        """
        生成组织 Schema
        
        Args:
            name: 组织名称
            url: 组织网址
            logo_url: Logo URL
            description: 组织描述
            social_profiles: 社交媒体资料 {platform: url}
            contact_email: 联系邮箱
            phone: 联系电话
            
        Returns:
            JSON-LD 格式的字典
        """
        schema = {
            "@context": "https://schema.org",
            "@type": "Organization",
            "name": name,
            "url": url,
        }
        
        if logo_url:
            schema["logo"] = {
                "@type": "ImageObject",
                "url": logo_url,
            }
        
        if description:
            schema["description"] = description
        
        if social_profiles:
            schema["sameAs"] = list(social_profiles.values())
        
        if contact_email or phone:
            schema["contactPoint"] = {
                "@type": "ContactPoint",
            }
            if contact_email:
                schema["contactPoint"]["email"] = contact_email
            if phone:
                schema["contactPoint"]["telephone"] = phone
        
        return schema
    
    def generate_person_schema(
        self,
        name: str,
        job_title: str = "",
        description: str = "",
        image_url: str = "",
        url: str = "",
        social_profiles: Dict[str, str] = None
    ) -> Dict[str, Any]:
        """
        生成人物 Schema
        
        Args:
            name: 姓名
            job_title: 职位
            description: 个人描述
            image_url: 头像 URL
            url: 个人主页 URL
            social_profiles: 社交媒体资料
            
        Returns:
            JSON-LD 格式的字典
        """
        schema = {
            "@context": "https://schema.org",
            "@type": "Person",
            "name": name,
        }
        
        if job_title:
            schema["jobTitle"] = job_title
        
        if description:
            schema["description"] = description
        
        if image_url:
            schema["image"] = {
                "@type": "ImageObject",
                "url": image_url,
            }
        
        if url:
            schema["url"] = url
        
        if social_profiles:
            schema["sameAs"] = list(social_profiles.values())
        
        return schema
    
    def generate_website_schema(
        self,
        name: str,
        url: str,
        description: str = "",
        search_url: str = ""
    ) -> Dict[str, Any]:
        """
        生成网站 Schema
        
        Args:
            name: 网站名称
            url: 网站首页 URL
            description: 网站描述
            search_url: 搜索页面 URL（带 {search_term_string} 占位符）
            
        Returns:
            JSON-LD 格式的字典
        """
        schema = {
            "@context": "https://schema.org",
            "@type": "WebSite",
            "name": name,
            "url": url,
        }
        
        if description:
            schema["description"] = description
        
        if search_url:
            schema["potentialAction"] = {
                "@type": "SearchAction",
                "target": search_url,
                "query-input": "required name=search_term_string"
            }
        
        return schema
    
    def generate_faq_schema(
        self,
        questions: List[Dict[str, str]]
    ) -> Dict[str, Any]:
        """
        生成常见问题 Schema
        
        Args:
            questions: 问题列表，每项包含 'question' 和 'answer'
            
        Returns:
            JSON-LD 格式的字典
        """
        main_entities = []
        for qa in questions:
            main_entities.append({
                "@type": "Question",
                "name": qa['question'],
                "acceptedAnswer": {
                    "@type": "Answer",
                    "text": qa['answer']
                }
            })
        
        return {
            "@context": "https://schema.org",
            "@type": "FAQPage",
            "mainEntity": main_entities
        }
    
    def generate_image_schema(
        self,
        url: str,
        caption: str = "",
        width: int = 0,
        height: int = 0
    ) -> Dict[str, Any]:
        """
        生成图片 Schema
        
        Args:
            url: 图片 URL
            caption: 图片说明
            width: 宽度
            height: 高度
            
        Returns:
            JSON-LD 格式的字典
        """
        schema = {
            "@context": "https://schema.org",
            "@type": "ImageObject",
            "url": url,
        }
        
        if caption:
            schema["caption"] = caption
        
        if width and height:
            schema["width"] = width
            schema["height"] = height
        
        return schema
    
    def generate_video_schema(
        self,
        name: str,
        description: str,
        thumbnail_url: str,
        upload_date: str,
        content_url: str = "",
        embed_url: str = "",
        duration: str = ""
    ) -> Dict[str, Any]:
        """
        生成视频 Schema
        
        Args:
            name: 视频标题
            description: 视频描述
            thumbnail_url: 缩略图 URL
            upload_date: 上传日期 (ISO 8601)
            content_url: 视频文件 URL
            embed_url: 嵌入 URL
            duration: 时长 (ISO 8601 格式，如 PT1M30S)
            
        Returns:
            JSON-LD 格式的字典
        """
        schema = {
            "@context": "https://schema.org",
            "@type": "VideoObject",
            "name": name,
            "description": description,
            "thumbnailUrl": thumbnail_url,
            "uploadDate": upload_date,
        }
        
        if content_url:
            schema["contentUrl"] = content_url
        
        if embed_url:
            schema["embedUrl"] = embed_url
        
        if duration:
            schema["duration"] = duration
        
        return schema
    
    def to_json_ld(self, schema: Dict[str, Any]) -> str:
        """
        将 Schema 转换为 JSON-LD 字符串
        
        Args:
            schema: Schema 字典
            
        Returns:
            JSON-LD 字符串（可直接插入 HTML）
        """
        import json
        return json.dumps(schema, ensure_ascii=False, indent=2)
    
    def to_script_tag(self, schema: Dict[str, Any]) -> str:
        """
        将 Schema 转换为 script 标签
        
        Args:
            schema: Schema 字典
            
        Returns:
            完整的 script 标签字符串
        """
        json_ld = self.to_json_ld(schema)
        return f'<script type="application/ld+json">\n{json_ld}\n</script>'
    
    def _get_site_name(self) -> str:
        """获取网站名称（可配置）"""
        try:
            # 尝试从系统设置中读取
            from shared.models import SystemSetting
            return SystemSetting.get_value("site_name")
        except Exception:
            pass
        
        # 回退到默认值
        return "FastBlog"


# 全局实例
schema_generator = SchemaGenerator()
