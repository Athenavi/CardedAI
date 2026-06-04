"""
Hreflang 标签生成器
为多语言页面生成正确的 hreflang 标签，帮助搜索引擎理解多语言内容
"""

from typing import Dict, List, Any, Optional


class HreflangGenerator:
    """
    Hreflang 标签生成器
    
    功能:
    1. 根据当前页面和可用翻译生成 hreflang 标签
    2. 支持 x-default 回退
    3. 验证 hreflang 格式正确性
    4. 生成多语言 sitemap
    """
    
    def __init__(self):
        # 语言代码映射（ISO 639-1 + ISO 3166-1）
        self.language_codes = {
            "en": "en-US",
            "zh-CN": "zh-CN",
            "zh-TW": "zh-TW",
            "ja": "ja-JP",
            "ko": "ko-KR",
            "es": "es-ES",
            "fr": "fr-FR",
            "de": "de-DE",
            "ru": "ru-RU",
            "ar": "ar-SA",
            "pt": "pt-BR",
            "it": "it-IT"
        }
    
    def generate_hreflang_tags(
        self,
        current_url: str,
        translations: Dict[str, str],
        default_language: str = "en",
        include_x_default: bool = True
    ) -> List[Dict[str, str]]:
        """
        生成 hreflang 标签
        
        Args:
            current_url: 当前页面的 URL
            translations: 翻译字典 {language_code: url}
            default_language: 默认语言
            include_x_default: 是否包含 x-default
            
        Returns:
            hreflang 标签列表
        """
        tags = []
        
        # 添加当前页面
        current_lang = self._detect_language_from_url(current_url)
        if current_lang:
            tags.append({
                "rel": "alternate",
                "hreflang": self.language_codes.get(current_lang, current_lang),
                "href": current_url
            })
        
        # 添加所有翻译版本
        for lang_code, url in translations.items():
            hreflang_code = self.language_codes.get(lang_code, lang_code)
            
            # 验证 URL 格式
            if not self._validate_url(url):
                continue
            
            tags.append({
                "rel": "alternate",
                "hreflang": hreflang_code,
                "href": url
            })
        
        # 添加 x-default（可选）
        if include_x_default:
            default_url = translations.get(default_language, current_url)
            tags.append({
                "rel": "alternate",
                "hreflang": "x-default",
                "href": default_url
            })
        
        return tags
    
    def render_html_tags(self, tags: List[Dict[str, str]]) -> str:
        """
        将 hreflang 标签渲染为 HTML
        
        Args:
            tags: hreflang 标签列表
            
        Returns:
            HTML 字符串
        """
        html_lines = []
        
        for tag in tags:
            html_line = (
                f'<link rel="{tag["rel"]}" '
                f'hreflang="{tag["hreflang"]}" '
                f'href="{tag["href"]}" />'
            )
            html_lines.append(html_line)
        
        return "\n".join(html_lines)
    
    def generate_sitemap_entry(
        self,
        url: str,
        translations: Dict[str, str],
        lastmod: Optional[str] = None,
        changefreq: str = "weekly",
        priority: float = 0.8
    ) -> Dict[str, Any]:
        """
        生成 sitemap 条目（包含多语言信息）
        
        Args:
            url: 主 URL
            translations: 翻译字典
            lastmod: 最后修改时间
            changefreq: 更新频率
            priority: 优先级
            
        Returns:
            sitemap 条目
        """
        entry = {
            "loc": url,
            "lastmod": lastmod,
            "changefreq": changefreq,
            "priority": priority,
            "xhtml:link": []
        }
        
        # 添加所有语言的链接
        for lang_code, trans_url in translations.items():
            hreflang_code = self.language_codes.get(lang_code, lang_code)
            entry["xhtml:link"].append({
                "rel": "alternate",
                "hreflang": hreflang_code,
                "href": trans_url
            })
        
        return entry
    
    def validate_hreflang_pair(
        self,
        url1: str,
        lang1: str,
        url2: str,
        lang2: str
    ) -> Dict[str, Any]:
        """
        验证 hreflang 双向链接是否正确
        
        Args:
            url1: 第一个URL
            lang1: 第一个语言
            url2: 第二个URL
            lang2: 第二个语言
            
        Returns:
            验证结果
        """
        errors = []
        warnings = []
        
        # 检查语言代码格式
        if not self._validate_language_code(lang1):
            errors.append(f"无效的语言代码: {lang1}")
        
        if not self._validate_language_code(lang2):
            errors.append(f"无效的语言代码: {lang2}")
        
        # 检查 URL 格式
        if not self._validate_url(url1):
            errors.append(f"无效的 URL: {url1}")
        
        if not self._validate_url(url2):
            errors.append(f"无效的 URL: {url2}")
        
        # 检查是否是不同的语言
        if lang1 == lang2:
            warnings.append(f"两个URL使用相同的语言代码: {lang1}")
        
        # 检查域名是否相同（建议）
        domain1 = self._extract_domain(url1)
        domain2 = self._extract_domain(url2)
        
        if domain1 and domain2 and domain1 != domain2:
            warnings.append(f"不同域名的URL: {domain1} vs {domain2}")
        
        return {
            "valid": len(errors) == 0,
            "errors": errors,
            "warnings": warnings
        }
    
    def get_recommended_languages(self) -> List[Dict[str, str]]:
        """获取推荐的语言列表"""
        return [
            {"code": code, "name": name, "hreflang": self.language_codes.get(code, code)}
            for code, name in [
                ("en", "English"),
                ("zh-CN", "简体中文"),
                ("zh-TW", "繁體中文"),
                ("ja", "日本語"),
                ("ko", "한국어"),
                ("es", "Español"),
                ("fr", "Français"),
                ("de", "Deutsch"),
                ("ru", "Русский"),
                ("ar", "العربية")
            ]
        ]
    
    def _detect_language_from_url(self, url: str) -> Optional[str]:
        """从URL检测语言"""
        # 简单的语言检测逻辑
        # 实际项目中应该更复杂
        if "/zh-cn/" in url.lower() or ".cn" in url:
            return "zh-CN"
        elif "/zh-tw/" in url.lower() or ".tw" in url:
            return "zh-TW"
        elif "/ja/" in url.lower() or ".jp" in url:
            return "ja"
        elif "/ko/" in url.lower() or ".kr" in url:
            return "ko"
        elif "/es/" in url.lower() or ".es" in url:
            return "es"
        elif "/fr/" in url.lower() or ".fr" in url:
            return "fr"
        elif "/de/" in url.lower() or ".de" in url:
            return "de"
        else:
            return "en"
    
    def _validate_language_code(self, code: str) -> bool:
        """验证语言代码格式"""
        # 简单验证：应该是 xx 或 xx-XX 格式
        import re
        pattern = r'^[a-z]{2}(-[A-Z]{2})?$'
        return bool(re.match(pattern, code))
    
    def _validate_url(self, url: str) -> bool:
        """验证URL格式"""
        import re
        pattern = r'^https?://[^\s/$.?#].[^\s]*$'
        return bool(re.match(pattern, url))
    
    def _extract_domain(self, url: str) -> Optional[str]:
        """从URL提取域名"""
        try:
            from urllib.parse import urlparse
            parsed = urlparse(url)
            return parsed.netloc
        except:
            return None


# 全局实例
hreflang_generator = HreflangGenerator()
