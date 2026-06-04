# -*- coding: utf-8 -*-
"""filters.py 工具模块单元测试"""
from datetime import datetime, timedelta, UTC

import pytest

from src.utils.filters import json_filter, string_split, relative_time_filter, f2list, md2html


# ──────────────── JSON 过滤器 ────────────────

@pytest.mark.unit
class TestJsonFilter:
    """测试 json_filter 函数"""

    def test_valid_json_string(self):
        result = json_filter('{"key": "value"}')
        assert result == {"key": "value"}

    def test_valid_json_array(self):
        result = json_filter('[1, 2, 3]')
        assert result == [1, 2, 3]

    def test_dict_input_returns_dict(self):
        d = {"already": "dict"}
        assert json_filter(d) is d

    def test_invalid_json_returns_none(self):
        assert json_filter("not json") is None

    def test_non_string_non_dict_returns_none(self):
        assert json_filter(123) is None
        assert json_filter([1, 2]) is None

    def test_none_returns_none(self):
        assert json_filter(None) is None

    def test_empty_string(self):
        assert json_filter("") is None

    def test_json_nested(self):
        result = json_filter('{"a": {"b": [1, 2]}}')
        assert result == {"a": {"b": [1, 2]}}


# ──────────────── 字符串分割 ────────────────

@pytest.mark.unit
class TestStringSplit:
    """测试 string_split 函数"""

    def test_basic_split(self):
        assert string_split("a,b,c") == ["a", "b", "c"]

    def test_custom_delimiter(self):
        assert string_split("a|b|c", "|") == ["a", "b", "c"]

    def test_single_item(self):
        assert string_split("hello") == ["hello"]

    def test_empty_string(self):
        assert string_split("") == [""]

    def test_non_string_returns_empty(self):
        assert string_split(123) == []
        assert string_split(None) == []
        assert string_split(["a", "b"]) == []

    def test_split_with_spaces(self):
        result = string_split("a , b , c")
        assert result == ["a ", " b ", " c"]

    def test_semicolon_delimiter(self):
        assert string_split("tag1;tag2;tag3", ";") == ["tag1", "tag2", "tag3"]


# ──────────────── 相对时间过滤器 ────────────────

@pytest.mark.unit
class TestRelativeTimeFilter:
    """测试 relative_time_filter 函数"""

    def test_none_returns_unknown(self):
        assert relative_time_filter(None) == "未知时间"

    def test_just_now(self):
        now = datetime.now(UTC)
        result = relative_time_filter(now - timedelta(seconds=30))
        assert result == "刚刚"

    def test_minutes_ago(self):
        now = datetime.now(UTC)
        result = relative_time_filter(now - timedelta(minutes=5))
        assert "分钟前" in result

    def test_hours_ago(self):
        now = datetime.now(UTC)
        result = relative_time_filter(now - timedelta(hours=3))
        assert "小时前" in result

    def test_days_ago(self):
        now = datetime.now(UTC)
        result = relative_time_filter(now - timedelta(days=7))
        assert "天前" in result

    def test_old_date_shows_date(self):
        """超过 30 天应显示日期格式"""
        now = datetime.now(UTC)
        result = relative_time_filter(now - timedelta(days=60))
        assert "-" in result  # YYYY-MM-DD 格式

    def test_naive_datetime_treated_as_utc(self):
        """没有时区信息的 datetime 应被当作 UTC 处理"""
        now = datetime.now(UTC)
        naive_dt = (now - timedelta(seconds=30)).replace(tzinfo=None)
        result = relative_time_filter(naive_dt)
        assert result == "刚刚"

    def test_future_time_imminent(self):
        """未来不到1分钟的时间"""
        now = datetime.now(UTC)
        result = relative_time_filter(now + timedelta(seconds=30))
        assert result == "即将"

    def test_future_time_minutes(self):
        now = datetime.now(UTC)
        result = relative_time_filter(now + timedelta(minutes=5))
        assert "分钟后" in result

    def test_future_time_hours(self):
        now = datetime.now(UTC)
        result = relative_time_filter(now + timedelta(hours=2))
        assert "小时后" in result

    def test_future_time_days(self):
        now = datetime.now(UTC)
        result = relative_time_filter(now + timedelta(days=10))
        assert "-" in result  # 显示日期


# ──────────────── f2list 过滤器 ────────────────

@pytest.mark.unit
class TestF2List:
    """测试 f2list 函数"""

    def test_none_returns_empty(self):
        assert f2list(None) == []

    def test_string_default_delimiter(self):
        result = f2list("tag1;tag2;tag3")
        assert result == ["tag1", "tag2", "tag3"]

    def test_string_custom_delimiter(self):
        result = f2list("a,b,c", ",")
        assert result == ["a", "b", "c"]

    def test_string_with_spaces(self):
        result = f2list(" tag1 ; tag2 ; tag3 ")
        assert result == ["tag1", "tag2", "tag3"]

    def test_list_input_returns_list(self):
        result = f2list(["a", "b", "c"])
        assert result == ["a", "b", "c"]

    def test_list_with_delimited_strings(self):
        """列表中的字符串包含分隔符时应拆分"""
        result = f2list(["a;b", "c;d"])
        assert result == ["a", "b", "c", "d"]

    def test_non_string_non_list(self):
        result = f2list(123)
        assert result == ["123"]

    def test_empty_string(self):
        result = f2list("")
        assert result == []

    def test_string_only_separators(self):
        result = f2list(";;;")
        assert result == []

    def test_list_with_non_string_items(self):
        result = f2list([1, 2, 3])
        assert result == [1, 2, 3]


# ──────────────── Markdown 转 HTML ────────────────

@pytest.mark.unit
class TestMd2Html:
    """测试 md2html 函数"""

    def test_simple_paragraph(self):
        result = md2html("Hello world")
        assert "Hello world" in result
        assert "<p>" in result

    def test_heading(self):
        result = md2html("# Title")
        assert "<h1>" in result
        assert "Title" in result

    def test_bold(self):
        result = md2html("**bold text**")
        assert "<strong>" in result

    def test_italic(self):
        result = md2html("*italic text*")
        assert "<em>" in result

    def test_link(self):
        result = md2html("[link](http://example.com)")
        assert 'href="http://example.com"' in result

    def test_code_block(self):
        result = md2html("```python\nprint('hello')\n```")
        assert "print" in result
        assert "highlight" in result.lower() or "<code" in result

    def test_inline_code(self):
        result = md2html("use `code` here")
        assert "<code>" in result

    def test_empty_input(self):
        result = md2html("")
        assert isinstance(result, str)

    def test_table(self):
        md = "| A | B |\n|---|---|\n| 1 | 2 |"
        result = md2html(md)
        assert "<table>" in result
        assert "<td>" in result

    def test_blockquote(self):
        result = md2html("> quoted text")
        assert "<blockquote>" in result

    def test_unordered_list(self):
        result = md2html("- item 1\n- item 2")
        assert "<ul>" in result
        assert "<li>" in result

    def test_ordered_list(self):
        result = md2html("1. first\n2. second")
        assert "<ol>" in result

    def test_result_contains_style(self):
        """输出应包含 <style> 标签"""
        result = md2html("# Test")
        assert "<style>" in result

    def test_result_contains_markdown_content_div(self):
        result = md2html("# Test")
        assert 'class="markdown-content"' in result

    def test_dark_theme(self):
        result = md2html("# Test", style_theme="dark")
        assert "#0d1117" in result  # dark theme bg color

    def test_horizontal_rule(self):
        result = md2html("---")
        assert "<hr" in result


# ──────────────── register_filters ────────────────

@pytest.mark.unit
class TestRegisterFilters:
    """测试 register_filters 返回的过滤器字典"""

    def test_returns_dict(self):
        from src.utils.filters import register_filters
        filters = register_filters()
        assert isinstance(filters, dict)

    def test_contains_expected_keys(self):
        from src.utils.filters import register_filters
        filters = register_filters()
        assert "json" in filters
        assert "string_split" in filters
        assert "md2html" in filters
        assert "relative_time" in filters
        assert "F2list" in filters

    def test_json_filter_callable(self):
        from src.utils.filters import register_filters
        filters = register_filters()
        assert callable(filters["json"])
        assert filters["json"]('{"key": 1}') == {"key": 1}
