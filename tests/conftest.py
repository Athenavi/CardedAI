# -*- coding: utf-8 -*-
"""
FastBlog Test Configuration

Shared fixtures and configuration for all tests.
"""

import asyncio
import os
from typing import Generator

import pytest

# Set test environment
os.environ.setdefault("ENVIRONMENT", "testing")
os.environ.setdefault("SECRET_KEY", "test-secret-key-for-testing-only")
os.environ.setdefault("JWT_SECRET_KEY", "test-jwt-secret-key")
os.environ.setdefault("DB_NAME", "fast_blog_test")


@pytest.fixture(scope="session")
def event_loop() -> Generator:
    """Create an instance of the default event loop for the test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture(scope="session")
def test_config() -> dict:
    """Test configuration dictionary."""
    return {
        "database_url": os.getenv(
            "DATABASE_URL",
            "postgresql+asyncpg://postgres:postgres@localhost:5432/fast_blog_test"
        ),
        "redis_url": os.getenv("REDIS_URL", "redis://localhost:6379/1"),
        "secret_key": "test-secret-key-for-testing-only",
    }


# Markers for test categorization
def pytest_configure(config):
    """Register custom markers."""
    config.addinivalue_line("markers", "unit: Unit tests")
    config.addinivalue_line("markers", "integration: Integration tests")
    config.addinivalue_line("markers", "slow: Slow tests")
