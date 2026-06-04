# FastBlog Development Makefile
# Usage: make <target>

.PHONY: help install dev test lint format clean docker-build docker-up docker-down dev-services-up dev-services-down dev-services-logs dev-services-search dev-services-tools pre-commit-install pre-commit-run

# Default target
help: ## Show this help message
	@echo "FastBlog Development Commands"
	@echo "============================="
	@echo ""
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-20s\033[0m %s\n", $$1, $$2}'

# ============================================================================
# Setup & Installation
# ============================================================================

install: ## Install all dependencies (backend + frontend)
	pip install -r requirements.txt
	cd frontend-astro && npm install
	@echo "✅ Dependencies installed successfully"

install-backend: ## Install backend dependencies only
	pip install -r requirements.txt
	@echo "✅ Backend dependencies installed"

install-frontend: ## Install frontend dependencies only
	cd frontend-astro && npm install
	@echo "✅ Frontend dependencies installed"

setup: ## Initial project setup (copy env, install deps)
	cp -n .env_example .env 2>/dev/null || true
	@echo "📝 Please edit .env with your configuration"
	$(MAKE) install

# ============================================================================
# Development
# ============================================================================

dev: ## Start development server (backend)
	python main.py --backend fastapi --env dev

dev-frontend: ## Start frontend development server
	cd frontend-astro && npm run dev

dev-all: ## Start both backend and frontend (requires two terminals)
	@echo "Starting backend on port 9421..."
	@echo "Starting frontend on port 4321..."
	@echo "Press Ctrl+C to stop"
	python main.py --backend fastapi --env dev &
	cd frontend-astro && npm run dev

# ============================================================================
# Testing
# ============================================================================

test: ## Run all tests
	python -m pytest tests/ -v

test-unit: ## Run unit tests only
	python -m pytest tests/ -v -m "unit"

test-integration: ## Run integration tests only
	python -m pytest tests/ -v -m "integration"

test-coverage: ## Run tests with coverage report
	python -m pytest tests/ --cov=src --cov-report=html --cov-report=term
	@echo "📊 Coverage report generated in htmlcov/"

test-frontend: ## Run frontend tests
	cd frontend-astro && npm test

# ============================================================================
# Code Quality
# ============================================================================

lint: ## Run linters
	@echo "🔍 Running Python linter..."
	python -m flake8 src/ --max-line-length=120 --ignore=E501,W503
	@echo "✅ Linting complete"

format: ## Format code with black and isort
	@echo "🎨 Formatting Python code..."
	python -m black src/ --line-length 120
	python -m isort src/ --profile black
	@echo "✅ Formatting complete"

type-check: ## Run type checking with mypy
	python -m mypy src/ --ignore-missing-imports

security-check: ## Run security checks
	@echo "🔒 Running security checks..."
	pip-audit
	python -m bandit -r src/ -ll

# ============================================================================
# Database
# ============================================================================

db-migrate: ## Create a new database migration
	alembic revision --autogenerate -m "$(msg)"

db-upgrade: ## Apply database migrations
	alembic upgrade head

db-downgrade: ## Rollback last database migration
	alembic downgrade -1

db-reset: ## Reset database (WARNING: destroys all data)
	@echo "⚠️  This will destroy all data. Press Ctrl+C to cancel."
	@sleep 3
	alembic downgrade base
	alembic upgrade head

# ============================================================================
# Docker
# ============================================================================

docker-build: ## Build Docker image
	docker build -t fastblog:latest .
	@echo "✅ Docker image built successfully"

docker-up: ## Start all services with Docker Compose
	docker-compose up -d
	@echo "✅ Services started. Visit http://localhost:4321"

docker-down: ## Stop all Docker services
	docker-compose down

docker-logs: ## View Docker logs
	docker-compose logs -f

docker-rebuild: ## Rebuild and restart Docker services
	docker-compose up -d --build

docker-clean: ## Clean Docker resources
	docker system prune -f
	docker volume prune -f

# ============================================================================
# Development Services (Docker)
# ============================================================================

dev-services-up: ## Start development services (PostgreSQL + Redis)
	docker-compose -f docker-compose.dev.yml up -d
	@echo "✅ Dev services started: PostgreSQL(5432) + Redis(6379)"

dev-services-down: ## Stop development services
	docker-compose -f docker-compose.dev.yml down

dev-services-logs: ## View development services logs
	docker-compose -f docker-compose.dev.yml logs -f

dev-services-search: ## Start dev services with Meilisearch
	docker-compose -f docker-compose.dev.yml --profile search up -d
	@echo "✅ Dev services started: PostgreSQL(5432) + Redis(6379) + Meilisearch(7700)"

dev-services-tools: ## Start dev services with Adminer + Redis Commander
	docker-compose -f docker-compose.dev.yml --profile tools --profile search up -d
	@echo "✅ Dev services started with tools: Adminer(8080) Redis Commander(8081) Meilisearch(7700)"

dev-services-reset: ## Reset development services (destroy volumes)
	docker-compose -f docker-compose.dev.yml down -v
	@echo "⚠️  Dev services stopped and volumes removed"

# ============================================================================
# Pre-commit Hooks
# ============================================================================

pre-commit-install: ## Install pre-commit hooks
	pip install pre-commit
	pre-commit install
	pre-commit install --hook-type pre-push
	@echo "✅ Pre-commit hooks installed"

pre-commit-run: ## Run all pre-commit hooks
	pre-commit run --all-files

pre-commit-update: ## Update pre-commit hooks
	pre-commit autoupdate

# ============================================================================
# Build & Release
# ============================================================================

build: ## Build production assets
	cd frontend-astro && npm run build
	@echo "✅ Production assets built"

build-release: ## Build release package
	python scripts/build_release.py --version $(version) --output release

# ============================================================================
# Maintenance
# ============================================================================

clean: ## Clean temporary files
	find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete 2>/dev/null || true
	find . -type d -name ".pytest_cache" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name "htmlcov" -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name ".coverage" -delete 2>/dev/null || true
	rm -rf build/ dist/ *.egg-info/
	@echo "✅ Cleaned temporary files"

backup: ## Create a backup
	python scripts/backup.sh
	@echo "✅ Backup created"

# ============================================================================
# CLI
# ============================================================================

cli: ## Run FastBlog CLI
	python scripts/cli.py $(cmd)

create-admin: ## Create admin user
	python scripts/cli.py create-admin

routes: ## List all API routes
	python scripts/cli.py routes
