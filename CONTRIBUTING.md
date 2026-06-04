# Contributing to FastBlog

Thank you for your interest in contributing to FastBlog! This document provides guidelines and information about
contributing to this project.

## 📋 Table of Contents

- [Code of Conduct](#code-of-conduct)
- [Getting Started](#getting-started)
- [Development Setup](#development-setup)
- [Making Changes](#making-changes)
- [Commit Convention](#commit-convention)
- [Pull Request Process](#pull-request-process)
- [Coding Standards](#coding-standards)
- [Testing](#testing)
- [Documentation](#documentation)

## Code of Conduct

This project follows our [Code of Conduct](CODE_OF_CONDUCT.md). By participating, you are expected to uphold this code.
Please report unacceptable behavior via the contact information in the Code of Conduct.

## Getting Started

### Ways to Contribute

- 🐛 **Report Bugs** — Found something
  broken? [Open an issue](https://github.com/Athenavi/fast_blog/issues/new?template=bug_report.md)
- 💡 **Suggest Features** — Have an idea? [Start a discussion](https://github.com/Athenavi/fast_blog/discussions/new)
- 📝 **Improve Documentation** — Fix typos, add examples, translate content
- 🧪 **Write Tests** — Help improve code coverage
- 🔧 **Fix Bugs** — Browse [open issues](https://github.com/Athenavi/fast_blog/issues?q=is%3Aissue+is%3Aopen+label%3Abug)
  and pick one
- ✨ **Add Features** — Check the [roadmap](https://github.com/Athenavi/fast_blog#-roadmap) for planned features

### First-Time Contributors

Look for issues labeled with [`good first issue`](https://github.com/Athenavi/fast_blog/labels/good%20first%20issue) —
these are specifically curated for newcomers.

## Development Setup

### Prerequisites

- Python 3.14+
- Node.js 18+
- PostgreSQL 16+
- Redis 7+
- Git

### Setup Steps

1. **Fork the repository**

   Click the "Fork" button on the [GitHub repository page](https://github.com/Athenavi/fast_blog).

2. **Clone your fork**

   ```bash
   git clone https://github.com/YOUR_USERNAME/fast_blog.git
   cd fast_blog
   ```

3. **Add upstream remote**

   ```bash
   git remote add upstream https://github.com/Athenavi/fast_blog.git
   ```

4. **Create a virtual environment**

   ```bash
   python -m venv venv
   source venv/bin/activate  # Linux/macOS
   # venv\Scripts\activate   # Windows
   ```

5. **Install dependencies**

   ```bash
   pip install -r requirements.txt
   ```

6. **Setup environment**

   ```bash
   cp .env.example .env
   # Edit .env with your local configuration
   ```

7. **Run database migrations**

   ```bash
   alembic upgrade head
   ```

8. **Start the development server**

    ```bash
    python main.py --port 9421 --env dev
    ```

9. **Setup frontend (optional)**

   ```bash
   cd frontend-astro
   npm install
   npm run dev
   ```

## Making Changes

### Branch Naming

Create a descriptive branch name:

```bash
git checkout -b feature/add-graphql-api
git checkout -b fix/login-redirect-bug
git checkout -b docs/update-api-reference
git checkout -b refactor/optimize-queries
```

Branch prefixes:

- `feature/` — New features
- `fix/` — Bug fixes
- `docs/` — Documentation changes
- `refactor/` — Code refactoring
- `test/` — Test additions/changes
- `chore/` — Maintenance tasks

### Code Changes

1. Make your changes in small, focused commits
2. Write or update tests for your changes
3. Ensure all tests pass
4. Update documentation if needed
5. Follow the [coding standards](#coding-standards)

## Commit Convention

We use [Conventional Commits](https://www.conventionalcommits.org/) for commit messages:

```
<type>(<scope>): <description>

[optional body]

[optional footer(s)]
```

### Types

| Type       | Description                           |
|------------|---------------------------------------|
| `feat`     | New feature                           |
| `fix`      | Bug fix                               |
| `docs`     | Documentation changes                 |
| `style`    | Code style changes (formatting, etc.) |
| `refactor` | Code refactoring                      |
| `perf`     | Performance improvements              |
| `test`     | Adding or updating tests              |
| `build`    | Build system changes                  |
| `ci`       | CI/CD changes                         |
| `chore`    | Maintenance tasks                     |

### Examples

```bash
feat(auth): add two-factor authentication support

- Implement TOTP-based 2FA
- Add QR code generation for authenticator apps
- Add backup codes support

Closes #123
```

```bash
fix(api): resolve article pagination offset error

The pagination was returning duplicate articles when using cursor-based
pagination with a non-zero offset.
```

## Pull Request Process

### Before Submitting

- [ ] Code follows the project's coding standards
- [ ] Self-review of code completed
- [ ] Tests added for new functionality
- [ ] All tests pass (`python -m pytest tests/`)
- [ ] Documentation updated if needed
- [ ] Commit messages follow conventional commits
- [ ] Branch is up-to-date with `main`

### PR Template

When creating a PR, please fill out the PR template completely:

1. **Description** — What does this PR do? Why?
2. **Type of Change** — Bug fix, feature, breaking change, etc.
3. **Testing** — How was this tested?
4. **Checklist** — Confirm all items are checked

### Review Process

1. A maintainer will review your PR within 7 days
2. Address any requested changes
3. Once approved, a maintainer will merge your PR
4. Your contribution will be included in the next release

### PR Size Guidelines

- **Small** (< 100 lines): Quick review
- **Medium** (100-500 lines): Standard review
- **Large** (500+ lines): May take longer; consider breaking into smaller PRs

## Coding Standards

### Python

- Follow [PEP 8](https://peps.python.org/pep-0008/) style guide
- Use type hints for all function signatures
- Maximum line length: 120 characters
- Use docstrings for all public functions and classes
- Use `async/await` for I/O-bound operations

```python
async def get_article(article_id: int, include_comments: bool = False) -> Article:
    """
    Retrieve an article by its ID.

    Args:
        article_id: The unique identifier of the article.
        include_comments: Whether to include article comments.

    Returns:
        The article object.

    Raises:
        ArticleNotFoundError: If the article does not exist.
    """
    ...
```

### JavaScript/TypeScript

- Use TypeScript for type safety
- Follow [ESLint](https://eslint.org/) configuration
- Use Prettier for formatting
- Prefer functional components in React

### General

- No commented-out code in production
- No `print()` statements in production code (use logging)
- No hardcoded values (use configuration)
- Write self-documenting code with clear variable names

## Testing

### Running Tests

```bash
# Run all tests
python -m pytest tests/

# Run with coverage
python -m pytest tests/ --cov=src --cov-report=html

# Run specific test file
python -m pytest tests/test_articles.py

# Run tests matching a pattern
python -m pytest tests/ -k "test_create"
```

### Writing Tests

- Place tests in the `tests/` directory
- Name test files as `test_<module>.py`
- Use descriptive test function names
- Use fixtures for common setup
- Aim for high coverage on new code

```python
import pytest
from src.models.article import Article

@pytest.fixture
def sample_article():
    return Article(title="Test Article", content="Test content")

def test_article_creation(sample_article):
    assert sample_article.title == "Test Article"
    assert sample_article.is_published is False

@pytest.mark.asyncio
async def test_async_article_fetch(async_client):
    response = await async_client.get("/api/v2/articles/1")
    assert response.status_code == 200
```

## Documentation

### Types of Documentation

1. **Code Comments** — Explain "why", not "what"
2. **Docstrings** — Document all public APIs
3. **README** — Keep project README up to date
4. **API Docs** — FastAPI auto-generates these; ensure endpoints are well-documented
5. **Guides** — Add to `docs/` for complex features

### Documentation Style

- Use clear, concise language
- Include code examples where helpful
- Keep documentation close to the code it describes
- Update docs when changing functionality

## 🏷️ Issue Labels

| Label              | Description                 |
|--------------------|-----------------------------|
| `bug`              | Something isn't working     |
| `feature`          | New feature request         |
| `documentation`    | Documentation improvements  |
| `good first issue` | Good for newcomers          |
| `help wanted`      | Extra attention needed      |
| `performance`      | Performance improvements    |
| `security`         | Security-related issues     |
| `breaking change`  | Introduces breaking changes |

## 📞 Getting Help

- **GitHub Discussions** — Ask questions and share ideas
- **GitHub Issues** — Report bugs and request features
- **Code Review** — Ask for feedback on your PR

## 🙏 Thank You

Your contributions make FastBlog better for everyone. Thank you for taking the time to contribute!
