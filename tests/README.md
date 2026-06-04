# FastBlog Test Suite

**适用版本**: FastBlog V0.3.26.0521+

This directory contains the test suite for FastBlog.

## Quick Start

```bash
# Run all tests
python -m pytest tests/

# Run with coverage
python -m pytest tests/ --cov=src --cov-report=html

# Run specific test category
python -m pytest tests/ -m unit          # Unit tests only
python -m pytest tests/ -m integration   # Integration tests only

# Run specific test file
python -m pytest tests/test_api.py -v
```

## Test Structure

```
tests/
├── conftest.py        # Shared fixtures and configuration
├── test_health.py     # Health check endpoint tests
├── test_models.py     # Data model unit tests
├── test_api.py        # API endpoint tests
└── README.md          # This file
```

## Writing Tests

### Test Naming Convention

- Test files: `test_<module>.py`
- Test classes: `Test<Feature>`
- Test functions: `test_<behavior>`

### Using Markers

```python
import pytest


@pytest.mark.unit
def test_fast_unit_test():
    assert True


@pytest.mark.integration
def test_database_integration():
    # Requires running database
    pass


@pytest.mark.slow
def test_long_running_operation():
    # Takes a long time to run
    pass
```

### Fixtures

Common fixtures are defined in `conftest.py`. Add project-wide fixtures there.

## CI/CD

Tests are automatically run on every push and pull request via GitHub Actions.
See `.github/workflows/ci.yml` for the CI configuration.
