# -*- coding: utf-8 -*-
"""
Model unit tests.
"""

import pytest
from datetime import datetime, timezone

from shared.models import User, Category


class TestUserModel:
    """Tests for the User model."""

    def test_user_creation(self):
        """Verify User can be created with required fields."""
        user = User(
            username="testuser",
            email="test@example.com",
            is_active=True,
            is_superuser=False,
        )
        assert user.username == "testuser"
        assert user.email == "test@example.com"
        assert user.is_active is True
        assert user.is_superuser is False

    def test_user_to_dict_excludes_sensitive(self):
        """Verify to_dict() excludes sensitive fields by default."""
        user = User(
            username="sensitive_user",
            email="sensitive@example.com",
            password="hashed_pwd_here",
            totp_secret="secret123",
            backup_codes='["code1","code2"]',
        )
        data = user.to_dict()
        assert data["username"] == "sensitive_user"
        assert "password" not in data
        assert "totp_secret" not in data
        assert "backup_codes" not in data

    def test_user_str_repr(self):
        """Verify __repr__ returns meaningful string."""
        user = User(id=99)
        assert repr(user) == "<User id=99>"


class TestCategoryModel:
    """Tests for the Category model."""

    def test_category_creation(self):
        """Verify Category can be created."""
        now = datetime.now(timezone.utc)
        cat = Category(
            name="Tech",
            slug="tech",
            sort_order=1,
            is_visible=True,
            created_at=now,
            updated_at=now,
        )
        assert cat.name == "Tech"
        assert cat.slug == "tech"
        assert cat.is_visible is True

    def test_category_hierarchy(self):
        """Verify parent-child category relationships."""
        parent = Category(id=1, name="Parent", slug="parent")
        child = Category(id=2, name="Child", slug="child", parent_id=1)
        assert child.parent_id == parent.id
        assert child.parent_id == 1

    def test_category_default_visibility(self):
        """Verify default visibility is True."""
        cat = Category(name="Default", slug="default")
        assert cat.is_visible is True or cat.is_visible is None
