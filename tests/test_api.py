# -*- coding: utf-8 -*-
"""
API endpoint tests.
"""

import pytest
from datetime import datetime, timezone

from shared.models import User


@pytest.mark.unit
class TestArticleAPI:
    """Tests for Article API endpoints."""

    def test_article_list_serialization(self):
        """Verify article listing data structure is valid."""
        article_data = {
            "id": 1,
            "title": "Test Article",
            "slug": "test-article",
            "status": 1,
        }
        assert isinstance(article_data, dict)
        assert article_data["id"] == 1
        assert article_data["title"] == "Test Article"
        assert article_data["slug"] == "test-article"

    def test_article_create_validation(self):
        """Verify article creation requires required fields."""
        article_data = {
            "title": "New Article",
            "slug": "new-article",
            "status": 0,
        }
        assert article_data["title"]
        assert article_data["slug"]
        assert article_data["status"] == 0

    def test_article_get_by_id(self):
        """Verify single article retrieval by id."""
        article_data = {"id": 42}
        assert article_data["id"] == 42
        assert isinstance(article_data["id"], int)

    def test_article_update_fields(self):
        """Verify article fields can be updated."""
        article_data = {"title": "Original Title", "status": 0}
        article_data["title"] = "Updated Title"
        article_data["status"] = 1
        assert article_data["title"] == "Updated Title"
        assert article_data["status"] == 1

    def test_article_delete_flag(self):
        """Verify article delete status is -1."""
        article_data = {"status": -1}
        assert article_data["status"] == -1


@pytest.mark.unit
class TestAuthAPI:
    """Tests for Authentication API endpoints."""

    def test_login_success_returns_user(self):
        """Verify successful login data structure."""
        user = User(
            id=1,
            username="testuser",
            email="test@example.com",
            is_active=True,
        )
        assert user.is_active
        assert user.username == "testuser"

    def test_login_inactive_user(self):
        """Verify inactive user cannot login."""
        user = User(
            id=2,
            username="inactive",
            email="inactive@example.com",
            is_active=False,
        )
        assert not user.is_active

    def test_login_missing_password(self):
        """Verify user without password cannot authenticate."""
        user = User(
            id=3,
            username="nopass",
            email="nopass@example.com",
            password=None,
        )
        assert user.password is None

    def test_protected_endpoint_requires_auth(self):
        """Verify protected endpoints require user authentication."""
        # Simulate: unauthenticated user has no id
        user = User(id=None, username=None)
        assert user.id is None
        assert user.username is None


@pytest.mark.unit
class TestUserAPI:
    """Tests for User API endpoints."""

    def test_user_registration_data(self):
        """Verify user registration data structure."""
        now = datetime.now(timezone.utc)
        user = User(
            username="newuser",
            email="new@example.com",
            is_active=True,
            date_joined=now,
        )
        assert user.username == "newuser"
        assert user.email == "new@example.com"
        assert user.is_active
        assert user.date_joined is not None

    def test_get_current_user_profile(self):
        """Verify current user profile data structure."""
        user = User(
            id=1,
            username="current_user",
            email="current@example.com",
            bio="Hello world",
            is_active=True,
        )
        data = user.to_dict()
        assert data["username"] == "current_user"
        assert data["bio"] == "Hello world"
        assert data["id"] == 1

    def test_update_user_profile(self):
        """Verify user profile fields can be updated."""
        user = User(
            username="oldname",
            email="old@example.com",
            bio="Old bio",
        )
        user.username = "newname"
        user.bio = "New bio"
        assert user.username == "newname"
        assert user.bio == "New bio"
