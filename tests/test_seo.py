# -*- coding: utf-8 -*-
"""seo.py 工具模块单元测试"""
import pytest

from src.utils.seo import slugify, generate_seo_friendly_url, get_feed_discovery_tags


@pytest.mark.unit
class TestSlugify:
    """测试 slugify 函数"""

    def test_simple_english(self):
        result = slugify("Hello World")
        assert result == "hello-world"

    def test_multiple_spaces(self):
        result = slugify("Hello   World")
        assert result == "hello-world"

    def test_special_characters(self):
        result = slugify("Hello, World! @#$%")
        assert result == "hello-world"

    def test_chinese_characters(self):
        """中文字符应被保留"""
        result = slugify("你好世界")
        assert "你好世界" in result

    def test_mixed_content(self):
        result = slugify("FastAPI 教程 2024")
        assert "fastapi" in result
        assert "2024" in result

    def test_empty_string(self):
        result = slugify("")
        assert result == ""

    def test_leading_trailing_dashes(self):
        result = slugify("--hello--")
        assert result == "hello"

    def test_underscores_preserved(self):
        result = slugify("hello_world")
        # underscores are not in the replacement set, should remain
        assert "hello" in result
        assert "world" in result


@pytest.mark.unit
class TestGenerateSeoFriendlyUrl:
    """测试 generate_seo_friendly_url 函数"""

    def test_article_url(self):
        url = generate_seo_friendly_url("Hello World", model_type="article")
        assert url.startswith("/p/")
        assert "hello-world" in url

    def test_category_url(self):
        url = generate_seo_friendly_url("Tech News", model_type="category")
        assert url.startswith("/category/")
        assert "tech-news" in url

    def test_tag_url(self):
        url = generate_seo_friendly_url("Python Tips", model_type="tag")
        assert url.startswith("/tag/")
        assert "python-tips" in url

    def test_other_type_url(self):
        url = generate_seo_friendly_url("Some Page", model_type="page")
        assert url.startswith("/")

    def test_empty_slug_fallback_article(self):
        """slug 为空时应使用 id 回退"""
        url = generate_seo_friendly_url("", model_type="article", id_value=42)
        assert "42" in url

    def test_empty_slug_fallback_category(self):
        url = generate_seo_friendly_url("", model_type="category", id_value=10)
        assert "10" in url

    def test_empty_slug_fallback_tag(self):
        url = generate_seo_friendly_url("", model_type="tag", id_value=5)
        assert "5" in url

    def test_empty_slug_no_id_article(self):
        """既无 slug 又无 id 时的回退"""
        url = generate_seo_friendly_url("", model_type="article")
        assert url == "/article.html"


@pytest.mark.unit
class TestGetFeedDiscoveryTags:
    """测试 get_feed_discovery_tags 函数"""

    def test_default_base_url(self):
        tags = get_feed_discovery_tags()
        assert "http://localhost:8000" in tags["rss_link"]
        assert "http://localhost:8000" in tags["atom_link"]

    def test_custom_base_url(self):
        tags = get_feed_discovery_tags("https://blog.example.com")
        assert tags["rss_link"] == "https://blog.example.com/api/v1/feed/rss"
        assert tags["atom_link"] == "https://blog.example.com/api/v1/feed/atom"

    def test_rss_xml_contains_link(self):
        tags = get_feed_discovery_tags("https://example.com")
        assert "rss+xml" in tags["rss_xml"]
        assert "https://example.com/api/v1/feed/rss" in tags["rss_xml"]

    def test_atom_xml_contains_link(self):
        tags = get_feed_discovery_tags("https://example.com")
        assert "atom+xml" in tags["atom_xml"]
        assert "https://example.com/api/v1/feed/atom" in tags["atom_xml"]

    def test_none_base_url_uses_default(self):
        tags = get_feed_discovery_tags(None)
        assert "localhost:8000" in tags["rss_link"]

    def test_empty_base_url_uses_default(self):
        tags = get_feed_discovery_tags("")
        assert "localhost:8000" in tags["rss_link"]

    def test_returns_four_keys(self):
        tags = get_feed_discovery_tags()
        assert set(tags.keys()) == {"rss_link", "atom_link", "rss_xml", "atom_xml"}
