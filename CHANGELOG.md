# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added

- **Backend**: FastAPI DDD modular architecture with 21 business modules (M00–M21)
  - M00 `products/`: Product / Iteration / Requirement three-tier management (full implementation)
  - `auth/`: JWT authentication + bcrypt password hashing (full implementation)
  - M01–M21 module skeletons: uda, import_clean, diagnosis, scene_map, generation, testcases, diff, coverage, test_plan, templates, knowledge, export, execution, analytics, notification, search, collaboration, dashboard, audit, recycle
  - `audit/models.py`: Full `AuditLog` model
  - `notification/models.py`: Full `Notification` model
- **Backend toolchain**: uv (environment), ruff (lint/format), pyright (type check), pytest + pytest-asyncio (testing)
- **Backend infrastructure**: SQLAlchemy 2.0 async engine (lazy-loaded), Alembic migrations, Celery + Redis worker
- **Frontend**: Next.js 16 App Router with TypeScript, Tailwind CSS v4, Ant Design v6
  - 15 page routes covering all business modules
  - Shared: Zustand stores, SSE hook, API client, type definitions
- **Frontend toolchain**: bun (package manager), Biome (lint/format), TypeScript strict mode
- **Infrastructure**: Docker Compose with PostgreSQL 16, Redis 7, Qdrant, MinIO (all with healthchecks)
- **CI/CD**: GitHub Actions workflows for backend (ruff + pyright + pytest), frontend (biome + tsc + build), docs (markdownlint + change detection)
- **Developer experience**: `init.sh` one-click environment setup, `CLAUDE.md` project guidelines, `.editorconfig`, `.env.example`
- **Documentation**: Design document and implementation plan in `docs/plans/`
