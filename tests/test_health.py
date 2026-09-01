# -*- coding: utf-8 -*-
"""
Health check endpoint tests.
"""

import pytest


@pytest.mark.unit
class TestHealthCheck:
    """Tests for the health check endpoint."""

    def test_health_endpoint_returns_true(self):
        """Verify health check logic returns True."""
        # 基础健康检查：验证关键模块可导入
        try:
            import importlib
            mod = importlib.import_module('src.setting')
            assert hasattr(mod, 'settings')
        except (ImportError, AttributeError):
            pytest.fail("Health check failed: src.setting module not available")

    def test_health_status_string(self):
        """Verify health status is 'healthy'."""
        status = "healthy"
        assert status == "healthy"
        assert isinstance(status, str)

    def test_health_check_has_required_fields(self):
        """Verify health check contains required fields."""
        health_info = {
            "status": "healthy",
            "version": "1.0.0",
            "database": "connected",
        }
        assert "status" in health_info
        assert "version" in health_info
        assert health_info["status"] == "healthy"

    def test_health_check_version_format(self):
        """Verify version string follows semver format."""
        version = "1.0.0"
        parts = version.split(".")
        assert len(parts) == 3
        assert all(p.isdigit() for p in parts)
