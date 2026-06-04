# -*- coding: utf-8 -*-
"""Unit tests for src/utils/security/safe.py and password_validator.py"""
import pytest

from src.utils.security.password_validator import hash_password, verify_password
from src.utils.security.safe import (
    validate_input, validate_xss, sanitize_sql_identifier, safe_query_builder,
    escape_html, validate_url, validate_password_strength, sanitize_filename,
    validate_integer, validate_boolean, is_valid_iso_language_code,
    validate_email_base, is_valid_hash,
)


@pytest.mark.unit
class TestValidateInput:
    """Test validate_input function"""

    def test_none_input_returns_true(self):
        is_valid, cleaned = validate_input(None)
        assert is_valid is True
        assert cleaned is None

    def test_normal_string_passes(self):
        is_valid, cleaned = validate_input("hello world")
        assert is_valid is True
        assert cleaned == "hello world"

    def test_strips_whitespace(self):
        is_valid, cleaned = validate_input("  hello  ")
        assert is_valid is True
        assert cleaned == "hello"

    def test_sql_injection_union_select(self):
        is_valid, _ = validate_input("1 UNION SELECT * FROM users")
        assert is_valid is False

    def test_sql_injection_drop_table(self):
        is_valid, _ = validate_input("'; DROP TABLE users; --")
        assert is_valid is False

    def test_sql_injection_comment(self):
        is_valid, _ = validate_input("admin' --")
        assert is_valid is False

    def test_allowed_pattern_match(self):
        is_valid, cleaned = validate_input("abc123", allowed_pattern=r'^[a-z0-9]+$')
        assert is_valid is True
        assert cleaned == "abc123"

    def test_allowed_pattern_mismatch(self):
        is_valid, _ = validate_input("abc@123", allowed_pattern=r'^[a-z0-9]+$')
        assert is_valid is False


@pytest.mark.unit
class TestValidateXSS:
    """Test validate_xss function"""

    def test_none_input(self):
        assert validate_xss(None) is True

    def test_normal_string(self):
        assert validate_xss("hello world") is True

    def test_script_tag(self):
        assert validate_xss("<script>alert('xss')</script>") is False

    def test_iframe_tag(self):
        assert validate_xss("<iframe src='evil'></iframe>") is False

    def test_event_handler(self):
        assert validate_xss("<img onerror=alert(1)>") is False

    def test_javascript_protocol(self):
        assert validate_xss("javascript:alert(1)") is False


@pytest.mark.unit
class TestSanitizeSqlIdentifier:
    """Test sanitize_sql_identifier function"""

    def test_valid_identifier(self):
        assert sanitize_sql_identifier("users") == "users"

    def test_valid_with_underscore(self):
        assert sanitize_sql_identifier("user_name") == "user_name"

    def test_empty_returns_empty(self):
        assert sanitize_sql_identifier("") == ""

    def test_none_returns_none(self):
        assert sanitize_sql_identifier(None) is None

    def test_invalid_starts_with_digit(self):
        with pytest.raises(ValueError):
            sanitize_sql_identifier("1table")

    def test_invalid_special_chars(self):
        with pytest.raises(ValueError):
            sanitize_sql_identifier("table; DROP")

    def test_invalid_too_long(self):
        with pytest.raises(ValueError):
            sanitize_sql_identifier("a" * 65)


@pytest.mark.unit
class TestSafeQueryBuilder:
    """Test safe_query_builder function"""

    def test_basic_query(self):
        result = safe_query_builder("users")
        assert "SELECT * FROM users" in result.text

    def test_with_conditions(self):
        result = safe_query_builder("users", conditions={"name": "test"})
        assert "WHERE" in result.text
        assert "name = :name" in result.text

    def test_with_order_and_limit(self):
        result = safe_query_builder("users", order_by="id", limit=10)
        assert "ORDER BY id" in result.text
        assert "LIMIT 10" in result.text

    def test_invalid_table_name(self):
        with pytest.raises(ValueError):
            safe_query_builder("users; DROP")


@pytest.mark.unit
class TestEscapeHtml:
    """Test escape_html function"""

    def test_none_input(self):
        assert escape_html(None) is None

    def test_empty_string(self):
        assert escape_html("") == ""

    def test_no_special_chars(self):
        assert escape_html("hello") == "hello"

    def test_ampersand(self):
        assert escape_html("a&b") == "a" + chr(38) + "amp;b"

    def test_less_than(self):
        assert escape_html("a<b") == "a" + chr(38) + "lt;b"

    def test_greater_than(self):
        assert escape_html("a>b") == "a" + chr(38) + "gt;b"

    def test_double_quote(self):
        assert escape_html('a' + chr(34) + 'b') == 'a' + chr(38) + 'quot;b'

    def test_single_quote(self):
        assert escape_html("a" + chr(39) + "b") == "a" + chr(38) + "#x27;b"

    def test_all_special_chars(self):
        result = escape_html("a&b<c>d")
        assert chr(38) + "amp;" in result
        assert chr(38) + "lt;" in result
        assert chr(38) + "gt;" in result

    def test_numeric_input(self):
        assert escape_html(123) == "123"


@pytest.mark.unit
class TestValidateUrl:
    """Test validate_url function"""

    def test_valid_http(self):
        is_valid, url = validate_url("http://example.com")
        assert is_valid is True
        assert url == "http://example.com"

    def test_valid_https(self):
        is_valid, url = validate_url("https://example.com/path?q=1")
        assert is_valid is True

    def test_empty_url(self):
        is_valid, url = validate_url("")
        assert is_valid is True

    def test_none_url(self):
        is_valid, url = validate_url(None)
        assert is_valid is True

    def test_javascript_scheme_rejected(self):
        is_valid, _ = validate_url("javascript:alert(1)")
        assert is_valid is False

    def test_custom_allowed_schemes(self):
        is_valid, _ = validate_url("ftp://files.example.com", allowed_schemes=['ftp'])
        assert is_valid is True

    def test_scheme_not_allowed(self):
        is_valid, _ = validate_url("ftp://files.example.com", allowed_schemes=['http', 'https'])
        assert is_valid is False


@pytest.mark.unit
class TestValidatePasswordStrength:
    """Test validate_password_strength function"""

    def test_strong_password(self):
        is_valid, _ = validate_password_strength("Abc123!@#")
        assert is_valid is True

    def test_too_short(self):
        is_valid, _ = validate_password_strength("Ab1!")
        assert is_valid is False

    def test_no_uppercase(self):
        is_valid, _ = validate_password_strength("abc123!@#")
        assert is_valid is False

    def test_no_lowercase(self):
        is_valid, _ = validate_password_strength("ABC123!@#")
        assert is_valid is False

    def test_no_digit(self):
        is_valid, _ = validate_password_strength("Abcdef!@#")
        assert is_valid is False

    def test_no_special_char(self):
        is_valid, _ = validate_password_strength("Abcdef123")
        assert is_valid is False


@pytest.mark.unit
class TestSanitizeFilename:
    """Test sanitize_filename function"""

    def test_normal_filename(self):
        assert sanitize_filename("test.txt") == "test.txt"

    def test_empty_filename(self):
        assert sanitize_filename("") == ""

    def test_none_filename(self):
        assert sanitize_filename(None) is None

    def test_path_traversal_removed(self):
        result = sanitize_filename("../../../etc/passwd")
        assert ".." not in result

    def test_special_chars_replaced(self):
        result = sanitize_filename("file name@#.txt")
        assert "@" not in result
        assert "#" not in result


@pytest.mark.unit
class TestValidateInteger:
    """Test validate_integer function"""

    def test_valid_integer(self):
        is_valid, val = validate_integer("42")
        assert is_valid is True
        assert val == 42

    def test_within_range(self):
        is_valid, val = validate_integer("5", min_val=1, max_val=10)
        assert is_valid is True
        assert val == 5

    def test_below_min(self):
        is_valid, _ = validate_integer("0", min_val=1)
        assert is_valid is False

    def test_above_max(self):
        is_valid, _ = validate_integer("100", max_val=50)
        assert is_valid is False

    def test_non_numeric(self):
        is_valid, _ = validate_integer("abc")
        assert is_valid is False

    def test_none_value(self):
        is_valid, _ = validate_integer(None)
        assert is_valid is False


@pytest.mark.unit
class TestValidateBoolean:
    """Test validate_boolean function"""

    def test_bool_true(self):
        is_valid, val = validate_boolean(True)
        assert is_valid is True
        assert val is True

    def test_bool_false(self):
        is_valid, val = validate_boolean(False)
        assert is_valid is True
        assert val is False

    def test_string_true(self):
        is_valid, val = validate_boolean("true")
        assert is_valid is True
        assert val is True

    def test_string_false(self):
        is_valid, val = validate_boolean("false")
        assert is_valid is True
        assert val is False

    def test_int_one(self):
        is_valid, val = validate_boolean(1)
        assert is_valid is True
        assert val is True

    def test_int_zero(self):
        is_valid, val = validate_boolean(0)
        assert is_valid is True
        assert val is False

    def test_invalid_string(self):
        is_valid, _ = validate_boolean("maybe")
        assert is_valid is False


@pytest.mark.unit
class TestValidateEmail:
    """Test validate_email_base function"""

    def test_valid_email(self):
        assert validate_email_base("user@example.com") is True

    def test_valid_with_dots(self):
        assert validate_email_base("first.last@example.co.uk") is True

    def test_invalid_no_at(self):
        assert validate_email_base("userexample.com") is False

    def test_invalid_no_domain(self):
        assert validate_email_base("user@") is False


@pytest.mark.unit
class TestIsValidHash:
    """Test is_valid_hash function"""

    def test_valid_sha256(self):
        sha256 = "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855"
        assert is_valid_hash(64, sha256) is True

    def test_valid_md5(self):
        md5 = "d41d8cd98f00b204e9800998ecf8427e"
        assert is_valid_hash(32, md5) is True

    def test_invalid_length(self):
        assert is_valid_hash(64, "abc123") is False

    def test_none_hash(self):
        assert is_valid_hash(64, None) is False

    def test_invalid_chars(self):
        assert is_valid_hash(4, "xyz!") is False

    def test_not_string(self):
        assert is_valid_hash(64, 12345) is False


@pytest.mark.unit
class TestIsValidLanguageCode:
    """Test is_valid_iso_language_code function"""

    def test_valid_en_us(self):
        assert is_valid_iso_language_code("en-US") is True

    def test_valid_zh_cn(self):
        assert is_valid_iso_language_code("zh-CN") is True

    def test_invalid_code(self):
        assert is_valid_iso_language_code("xx-YY") is False

    def test_empty_string(self):
        assert is_valid_iso_language_code("") is False


@pytest.mark.unit
class TestPasswordValidator:
    """Test hash_password and verify_password functions"""

    def test_hash_returns_string(self):
        h = hash_password("TestPass123!")
        assert isinstance(h, str)
        assert len(h) > 0

    def test_verify_correct_password(self):
        h = hash_password("TestPass123!")
        assert verify_password("TestPass123!", h) is True

    def test_verify_wrong_password(self):
        h = hash_password("TestPass123!")
        assert verify_password("WrongPass1!", h) is False

    def test_verify_invalid_hash(self):
        assert verify_password("TestPass123!", "not-a-valid-hash") is False
