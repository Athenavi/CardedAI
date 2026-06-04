# -*- coding: utf-8 -*-
"""field_filter.py 工具模块单元测试"""
import pytest

from src.utils.field_filter import filter_fields, parse_fields_param, validate_fields


@pytest.mark.unit
class TestFilterFields:
    """测试 filter_fields 函数"""

    def test_no_fields_param_returns_original(self):
        data = {"id": 1, "title": "Test", "content": "Hello"}
        result = filter_fields(data, None)
        assert result == data

    def test_empty_fields_param_returns_original(self):
        data = {"id": 1, "title": "Test"}
        result = filter_fields(data, "")
        assert result == data

    def test_whitespace_fields_param_returns_original(self):
        data = {"id": 1, "title": "Test"}
        result = filter_fields(data, "   ")
        assert result == data

    def test_single_field(self):
        data = {"id": 1, "title": "Test", "content": "Hello"}
        result = filter_fields(data, "title")
        assert result == {"title": "Test"}

    def test_multiple_fields(self):
        data = {"id": 1, "title": "Test", "content": "Hello", "status": "published"}
        result = filter_fields(data, "id,title")
        assert result == {"id": 1, "title": "Test"}

    def test_fields_with_spaces(self):
        data = {"id": 1, "title": "Test", "content": "Hello"}
        result = filter_fields(data, " id , title ")
        assert result == {"id": 1, "title": "Test"}

    def test_nonexistent_field_ignored(self):
        data = {"id": 1, "title": "Test"}
        result = filter_fields(data, "id,nonexistent")
        assert result == {"id": 1}

    def test_nested_field(self):
        data = {
            "id": 1,
            "title": "Test",
            "author": {"id": 2, "username": "admin", "email": "a@b.com"},
        }
        result = filter_fields(data, "id,author.username")
        assert result == {"id": 1, "author": {"username": "admin"}}

    def test_deeply_nested_field(self):
        data = {
            "id": 1,
            "author": {"profile": {"bio": "hello", "avatar": "url"}},
        }
        result = filter_fields(data, "id,author.profile.bio")
        assert result == {"id": 1, "author": {"profile": {"bio": "hello"}}}

    def test_list_data(self):
        data = [
            {"id": 1, "title": "A", "content": "..."},
            {"id": 2, "title": "B", "content": "..."},
        ]
        result = filter_fields(data, "id,title")
        assert result == [{"id": 1, "title": "A"}, {"id": 2, "title": "B"}]

    def test_non_dict_non_list_returns_as_is(self):
        result = filter_fields("simple string", "field")
        assert result == "simple string"

    def test_nested_field_missing_parent(self):
        """当嵌套字段的父级不存在时，应安全跳过"""
        data = {"id": 1, "title": "Test"}
        result = filter_fields(data, "id,author.username")
        assert result == {"id": 1}

    def test_nested_field_parent_not_dict(self):
        """当嵌套字段的父级不是字典时，应安全跳过"""
        data = {"id": 1, "author": "simple_string"}
        result = filter_fields(data, "id,author.username")
        assert result == {"id": 1}

    def test_multiple_nested_fields_same_parent(self):
        data = {
            "id": 1,
            "author": {"id": 2, "username": "admin", "email": "a@b.com"},
        }
        result = filter_fields(data, "id,author.username,author.email")
        assert result == {
            "id": 1,
            "author": {"username": "admin", "email": "a@b.com"},
        }


@pytest.mark.unit
class TestParseFieldsParam:
    """测试 parse_fields_param 函数"""

    def test_empty_string(self):
        assert parse_fields_param("") == []

    def test_none_input(self):
        assert parse_fields_param(None) == []

    def test_single_field(self):
        assert parse_fields_param("title") == ["title"]

    def test_multiple_fields(self):
        assert parse_fields_param("id,title,content") == ["id", "title", "content"]

    def test_fields_with_spaces(self):
        assert parse_fields_param(" id , title , content ") == ["id", "title", "content"]

    def test_nested_fields(self):
        result = parse_fields_param("id,author.username,author.email")
        assert result == ["id", "author.username", "author.email"]

    def test_empty_segments_ignored(self):
        """逗号间的空白段应被忽略"""
        assert parse_fields_param("id,,title,") == ["id", "title"]


@pytest.mark.unit
class TestValidateFields:
    """测试 validate_fields 函数"""

    def test_no_fields_param(self):
        data = {"id": 1, "title": "Test"}
        assert validate_fields(data, ["id", "title"], "") == []

    def test_all_valid_fields(self):
        data = {"id": 1, "title": "Test", "content": "..."}
        assert validate_fields(data, ["id", "title", "content"], "id,title") == []

    def test_some_invalid_fields(self):
        data = {"id": 1, "title": "Test"}
        invalid = validate_fields(data, ["id", "title"], "id,secret_field")
        assert invalid == ["secret_field"]

    def test_nested_field_valid_top_level(self):
        """嵌套字段只检查顶级字段名"""
        data = {"id": 1, "author": {"username": "admin"}}
        invalid = validate_fields(data, ["id", "author"], "id,author.username")
        assert invalid == []

    def test_nested_field_invalid_top_level(self):
        data = {"id": 1, "author": {"username": "admin"}}
        invalid = validate_fields(data, ["id", "author"], "id,secret.username")
        assert invalid == ["secret.username"]

    def test_multiple_invalid(self):
        data = {"id": 1}
        invalid = validate_fields(data, ["id"], "id,foo,bar")
        assert set(invalid) == {"foo", "bar"}

    def test_none_fields_param(self):
        assert validate_fields({}, ["id"], None) == []
