# Changelog

All notable changes to FastBlog will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added

- Bilingual documentation (English & Chinese)
- Comprehensive CI/CD pipeline
- Docker Compose production configuration
- Makefile for common development tasks
- Security policy documentation
- Root-level contributing guide
- EditorConfig for consistent formatting
- MCP (Model Context Protocol) Server for AI integration

### Changed

- Improved project documentation structure
- Enhanced README with better organization
- Updated all documentation to reflect V0.3 architecture

## [V0.3.26.0521] - 2026-05-21

### Added

- MCP Server for AI-powered content management
- Multi-site support with domain-based routing
- Zero-trust security middleware
- Performance monitoring middleware
- Accessibility optimizer
- Plugin hot-reload system (hot_load, hot_unload, hot_reload)
- Plugin dependency resolver with circular dependency detection
- Plugin manifest validator with template generation
- Mobile API V3 with dedicated endpoints
- Capacitor mobile app framework integration
- JavaScript SDK for frontend integration
- Python SDK with async client support
- Update server with backup/restore functionality
- Process supervisor for multi-process management
- Unified database manager with async session management
- SEO traffic tracking and keyword analysis
- Article view statistics service
- Token blacklist for JWT revocation
- Rate limiting middleware with configurable zones

### Changed

- Migrated from Django backend to pure FastAPI
- Upgraded to FastAPI 0.128.0
- Upgraded to Python 3.14+
- Upgraded to PostgreSQL 16+
- Upgraded to Astro 5.7 frontend with React 19 Islands
- Upgraded to TailwindCSS 4.x
- Plugin system imports moved to `shared.services.plugins.plugin_manager.core`
- Theme system migrated from Jinja2 to Astro components
- API routes restructured: V1 (deprecated, auto-redirects), V2 (primary), V3 (mobile)
- Static resource paths unified under `/assets/` prefix

### Removed

- Django backend support (V0.2+)
- Jinja2 template engine (replaced by Astro)
- Flask compatibility layer

## [V0.2.0] - 2025-06-01

### Added

- FastAPI as primary backend framework
- Astro frontend with Islands architecture
- Plugin system with WordPress-style Hook mechanism
- Theme engine with hot-reload capability
- RESTful API V2 with auto-generated Swagger docs
- JWT authentication with Cookie/Bearer dual-mode
- Two-factor authentication (TOTP)
- Role-based access control (RBAC)
- Article management system with rich text editor (TipTap)
- Comment system with nested replies
- Media management with image/video processing
- Full-text search (Meilisearch integration)
- SEO optimization toolkit with sitemap generation
- Docker Compose deployment configuration
- Nginx reverse proxy with rate limiting
- Redis caching layer
- Database migrations with Alembic
- Email notification system
- RSS feed support
- Backup and restore functionality

### Changed

- Backend architecture from Django to FastAPI
- Database ORM from Django ORM to SQLAlchemy 2.0 async
- Password hashing from Argon2id to bcrypt

## [0.1.0] - 2025-01-01

### Added

- Initial project setup
- Basic blog functionality
- User authentication
- Article CRUD operations
- Basic admin dashboard

[Unreleased]: https://github.com/Athenavi/fast_blog/compare/v0.2.0...HEAD

[V0.3.26.0521]: https://github.com/Athenavi/fast_blog/compare/v0.2.0...V0.3.26.0521

[V0.2.0]: https://github.com/Athenavi/fast_blog/compare/v0.1.0...v0.2.0
[0.1.0]: https://github.com/Athenavi/fast_blog/releases/tag/v0.1.0
