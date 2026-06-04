# -*- coding: utf-8 -*-
"""pagination.py 工具模块单元测试"""
import pytest

from src.utils.pagination import (
    PaginationParams,
    create_pagination_response,
    parse_sort_params,
    CursorPagination,
)


@pytest.mark.unit
class TestPaginationParams:
    """测试 PaginationParams 类"""

    def test_default_values(self):
        params = PaginationParams(page=1, per_page=20, sort_by=None, sort_order="desc")
        assert params.page == 1
        assert params.per_page == 20
        assert params.sort_by is None
        assert params.sort_order == "desc"

    def test_offset_page_1(self):
        params = PaginationParams(page=1, per_page=20)
        assert params.offset == 0

    def test_offset_page_3(self):
        params = PaginationParams(page=3, per_page=10)
        assert params.offset == 20

    def test_offset_page_5_per_page_25(self):
        params = PaginationParams(page=5, per_page=25)
        assert params.offset == 100

    def test_limit_property(self):
        params = PaginationParams(page=1, per_page=50)
        assert params.limit == 50

    def test_to_dict_full(self):
        params = PaginationParams(page=2, per_page=25, sort_by="created_at", sort_order="desc")
        d = params.to_dict()
        assert d["page"] == 2
        assert d["per_page"] == 25
        assert d["offset"] == 25
        assert d["limit"] == 25
        assert d["sort_by"] == "created_at"
        assert d["sort_order"] == "desc"

    def test_to_dict_defaults(self):
        params = PaginationParams(page=1, per_page=20, sort_by=None, sort_order="desc")
        d = params.to_dict()
        assert d["page"] == 1
        assert d["per_page"] == 20
        assert d["offset"] == 0
        assert d["limit"] == 20
        assert d["sort_by"] is None
        assert d["sort_order"] == "desc"


@pytest.mark.unit
class TestCreatePaginationResponse:
    """测试 create_pagination_response 函数"""

    def test_basic_response(self):
        data = [{"id": 1}, {"id": 2}]
        result = create_pagination_response(data, total=10, page=1, per_page=2)
        assert result["data"] == data
        assert result["pagination"]["current_page"] == 1
        assert result["pagination"]["per_page"] == 2
        assert result["pagination"]["total"] == 10
        assert result["pagination"]["total_pages"] == 5
        assert result["pagination"]["has_next"] is True
        assert result["pagination"]["has_prev"] is False

    def test_last_page(self):
        data = [{"id": 9}, {"id": 10}]
        result = create_pagination_response(data, total=10, page=5, per_page=2)
        assert result["pagination"]["has_next"] is False
        assert result["pagination"]["has_prev"] is True

    def test_middle_page(self):
        data = [{"id": 5}, {"id": 6}]
        result = create_pagination_response(data, total=10, page=3, per_page=2)
        assert result["pagination"]["has_next"] is True
        assert result["pagination"]["has_prev"] is True

    def test_single_page(self):
        data = [{"id": 1}]
        result = create_pagination_response(data, total=1, page=1, per_page=20)
        assert result["pagination"]["total_pages"] == 1
        assert result["pagination"]["has_next"] is False
        assert result["pagination"]["has_prev"] is False

    def test_empty_data(self):
        result = create_pagination_response([], total=0, page=1, per_page=20)
        assert result["data"] == []
        assert result["pagination"]["total"] == 0
        assert result["pagination"]["total_pages"] == 0

    def test_total_pages_ceil(self):
        """验证总页数向上取整"""
        result = create_pagination_response([], total=11, page=1, per_page=5)
        assert result["pagination"]["total_pages"] == 3

    def test_additional_data(self):
        data = [{"id": 1}]
        extra = {"filters": {"status": "published"}, "summary": {"count": 1}}
        result = create_pagination_response(data, total=1, page=1, per_page=20, additional_data=extra)
        assert result["filters"] == {"status": "published"}
        assert result["summary"] == {"count": 1}

    def test_per_page_zero(self):
        """per_page 为 0 时 total_pages 应为 0"""
        result = create_pagination_response([], total=10, page=1, per_page=0)
        assert result["pagination"]["total_pages"] == 0


@pytest.mark.unit
class TestParseSortParams:
    """测试 parse_sort_params 函数"""

    def test_no_sort_by(self):
        field, order = parse_sort_params(None)
        assert field is None
        assert order == "desc"

    def test_valid_sort_field(self):
        field, order = parse_sort_params("created_at", "asc", allowed_fields=["created_at", "title"])
        assert field == "created_at"
        assert order == "asc"

    def test_invalid_sort_field_raises(self):
        with pytest.raises(ValueError, match="Invalid sort field"):
            parse_sort_params("invalid_field", "desc", allowed_fields=["created_at", "title"])

    def test_invalid_order_defaults_to_desc(self):
        field, order = parse_sort_params("created_at", "invalid")
        assert field == "created_at"
        assert order == "desc"

    def test_no_allowed_fields_accepts_any(self):
        field, order = parse_sort_params("any_field", "asc")
        assert field == "any_field"
        assert order == "asc"

    def test_order_case_insensitive(self):
        field, order = parse_sort_params("created_at", "ASC")
        assert order == "asc"

        field, order = parse_sort_params("created_at", "DESC")
        assert order == "desc"

    def test_default_order(self):
        field, order = parse_sort_params("created_at")
        assert order == "desc"


@pytest.mark.unit
class TestCursorPagination:
    """测试 CursorPagination 类"""

    def test_default_values(self):
        cp = CursorPagination(cursor=None, limit=20, sort_by="id", sort_order="desc")
        assert cp.cursor is None
        assert cp.limit == 20
        assert cp.sort_by == "id"
        assert cp.sort_order == "desc"

    def test_where_clause_desc(self):
        cp = CursorPagination(cursor="100", limit=20, sort_by="id", sort_order="desc")
        clause = cp.get_where_clause(100)
        assert clause == "id < :cursor_value"

    def test_where_clause_asc(self):
        cp = CursorPagination(cursor="50", limit=20, sort_by="created_at", sort_order="asc")
        clause = cp.get_where_clause(50)
        assert clause == "created_at > :cursor_value"

    def test_create_response_with_more(self):
        cp = CursorPagination(cursor=None, limit=20, sort_by="id", sort_order="desc")
        data = [{"id": 10}, {"id": 9}]
        result = cp.create_response(data, has_more=True, next_cursor="8")
        assert result["data"] == data
        assert result["pagination"]["has_more"] is True
        assert result["pagination"]["next_cursor"] == "8"
        assert result["pagination"]["limit"] == 20
        assert result["pagination"]["sort_by"] == "id"
        assert result["pagination"]["sort_order"] == "desc"

    def test_create_response_no_more(self):
        cp = CursorPagination(cursor=None, limit=20, sort_by="id", sort_order="desc")
        data = [{"id": 1}]
        result = cp.create_response(data, has_more=False)
        assert result["pagination"]["has_more"] is False
        assert result["pagination"]["next_cursor"] is None

    def test_custom_sort(self):
        cp = CursorPagination(cursor=None, limit=10, sort_by="title", sort_order="asc")
        result = cp.create_response([], has_more=False)
        assert result["pagination"]["sort_by"] == "title"
        assert result["pagination"]["sort_order"] == "asc"
        assert result["pagination"]["limit"] == 10
