# AGENTS.md — AI Agent Guidelines for ZStack Helper

面向 AI Agent 的项目开发规范与约束。

## Project Overview

> **This is a Python FastAPI project. Use `uv` as package manager; fallback to `pip`. Runtime: Python 3.12+. Do NOT use Node.js/npm/bun.**

- **Purpose**: 基于 RAG 的智能工作助手，面向 ZStack 云计算工程师 / 售前 / 技术支持
- **Backend**: FastAPI + OpenAI + ChromaDB (向量检索)
- **Frontend**: 内置 SPA (vanilla HTML/CSS/JS)，FastAPI 静态服务
- **Architecture**: Monolith — API + Knowledge RAG + 9 Scenario Modules

## Build / Dev / Test Commands

```bash
# Development
uv run python main.py                     # Start dev server (localhost:8000)
uv run uvicorn main:app --reload          # Dev with auto-reload

# Linting & Formatting
uv run ruff check .                       # Lint (check only)
uv run ruff check . --fix                 # Lint (auto-fix)
uv run ruff format .                      # Format all files

# Type Checking
uv run mypy app/                          # Type check (if configured)

# Testing
uv run pytest                             # Run all tests
uv run pytest tests/test_api.py           # Run single test file
uv run pytest -k "test_health"            # Run tests matching pattern

# Dependencies
uv sync                                   # Install all dependencies
uv add <package>                          # Add production dependency
uv add --dev <package>                    # Add dev dependency

# Knowledge Base
curl -X POST http://localhost:8000/knowledge/bootstrap  # Init seed data (~1000 records)
```

## Code Style (Python)

### Formatting (Ruff)

- **Indent**: 4 spaces
- **Quotes**: Double `"`
- **Line length**: 120 chars
- **Import sorting**: isort-compatible, auto-organized by ruff

### Import Order

1. Standard library (`import os`, `import logging`)
2. Third-party packages (`from fastapi import ...`, `from pydantic import ...`)
3. Local modules (`from app.models.common import ...`, `from config import ...`)

```python
import logging
from typing import Optional

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from app.models.common import ScenarioType, OutputMode
from config import get_settings
```

### Naming Conventions

| Type           | Convention   | Example                   |
|----------------|-------------|---------------------------|
| Files          | snake_case   | `scenario_service.py`     |
| Classes        | PascalCase   | `BaseScenarioModule`      |
| Functions      | snake_case   | `get_vector_store`        |
| Constants      | UPPER_SNAKE  | `SCENARIO_MODULES`        |
| Variables      | snake_case   | `query_embedding`         |
| Pydantic Models| PascalCase   | `TroubleshootingInput`    |

### Error Handling

- Use `try-except` with specific exception types; avoid bare `except:`
- FastAPI: Raise `HTTPException` with proper status codes (400, 404, 500)
- Service layer: Let exceptions propagate; API layer catches and wraps
- Never use empty `except: pass`
- Log errors with `logger.error(f"Context: {e}")`

### Pydantic Models

- All request/response models use Pydantic v2 `BaseModel`
- Use `Field(default_factory=...)` for mutable defaults
- Use `Optional[str] = None` for optional fields
- Enum values: `str, Enum` pattern for JSON-serializable enums

## Architecture

```
zstack-helper/
├── main.py                     # FastAPI app entry point + lifespan
├── config.py                   # Pydantic Settings (env-based config)
├── pyproject.toml              # Dependencies + tool config (ruff, pytest)
│
├── app/
│   ├── auth.py                 # API Key middleware
│   ├── api/                    # FastAPI routers (thin layer)
│   │   ├── health.py           # GET /health
│   │   ├── knowledge.py        # /knowledge/* endpoints
│   │   └── scenarios.py        # /scenario/* endpoints (dynamic routing)
│   │
│   ├── services/               # Business logic orchestration
│   │   ├── knowledge_service.py
│   │   └── scenario_service.py
│   │
│   ├── models/                 # Pydantic data models
│   │   ├── common.py           # ScenarioType, OutputMode, ScenarioResult
│   │   ├── knowledge.py        # Search/Ingest request/response
│   │   └── scenarios.py        # Per-scenario input models
│   │
│   ├── scenario_modules/       # 9 scenario implementations
│   │   ├── base.py             # BaseScenarioModule (ABC)
│   │   ├── troubleshooting.py  # 技术排查
│   │   ├── tech_qa.py          # 技术问答
│   │   ├── customer_reply.py   # 客户答复
│   │   ├── weekly_report.py    # 周报生成
│   │   ├── briefing.py         # 汇报生成
│   │   ├── training.py         # 培训生成
│   │   ├── demo_prep.py        # 演示准备
│   │   ├── poc_support.py      # PoC 支持
│   │   └── escalation.py       # 问题升级
│   │
│   ├── prompt_templates/       # LLM prompt templates per scenario
│   │   ├── output_modes.py     # 客户/技术/领导模式 prompt
│   │   └── *.py                # Per-scenario prompts
│   │
│   ├── knowledge/              # RAG core
│   │   ├── vector_store.py     # ChromaDB wrapper (singleton)
│   │   ├── embeddings.py       # OpenAI Embedding (singleton)
│   │   ├── chunker.py          # Document chunking
│   │   └── dedup.py            # xxhash content dedup
│   │
│   ├── ingestion/              # Data ingestion pipeline
│   │   ├── file_ingestor.py    # File → chunks → embed → store
│   │   ├── url_ingestor.py     # URL → fetch → clean → chunks → store
│   │   ├── cleaner.py          # HTML/text cleaning (trafilatura)
│   │   └── bootstrap.py        # Seed data loader
│   │
│   └── router/
│       └── scenario_router.py  # Scenario registry + auto-detection
│
├── web/                        # Frontend SPA (served by FastAPI)
│   ├── index.html
│   ├── style.css
│   └── app.js
│
├── data/
│   └── seed/                   # Bootstrap JSON seed files
│
└── tests/                      # Pytest test suite
```

### Key Patterns

- **Singleton services**: `get_vector_store()`, `get_embedding_service()` use module-level `_instance` pattern
- **Scenario registry**: `SCENARIO_MODULES` dict maps `ScenarioType` → Module class
- **Dynamic routing**: `route_scenario()` instantiates + caches module, calls `module.execute()`
- **RAG pipeline**: Query → Embed → ChromaDB search → Context → LLM prompt → Response
- **Output modes**: Every scenario supports 3 output modes (customer/technical/leadership)

## Adding a New Scenario Module

1. **Prompt**: Create `app/prompt_templates/<name>.py` with `SYSTEM_PROMPT` and `USER_PROMPT`
2. **Module**: Create `app/scenario_modules/<name>.py` inheriting `BaseScenarioModule`
3. **Model**: Add input model in `app/models/scenarios.py`
4. **Enum**: Add to `ScenarioType` in `app/models/common.py`
5. **Registry**: Add to `SCENARIO_MODULES` in `app/router/scenario_router.py`
6. **Keywords**: Add to `SCENARIO_KEYWORDS` in `app/router/scenario_router.py`
7. **API**: The dynamic endpoint `POST /scenario/{scenario_type}` handles it automatically

## Environment Variables

- Use `pydantic-settings` with `.env` file (see `.env.example`)
- Access via `get_settings()` (cached singleton)
- Never commit `.env` files; keep `.env.example` updated
- Required: `OPENAI_API_KEY`
- Optional: `AUTH_API_KEY` (enables API key auth)

## Development Principles

> **These principles apply to ALL code changes.**

1. **安全第一** — 所有涉及基础设施操作（K8s、ZStack API 调用、存储操作）必须有安全检查，危险操作需确认
2. **知识驱动** — 基于 RAG 知识库确保回答准确，避免幻觉
3. **结论先行** — 先给结论，再给解释；输出可直接使用
4. **同步文档** — 代码变更时同步更新 AGENTS.md 和相关文档

## Critical Rules

**DO:**
- Run `ruff check . --fix && ruff format .` before committing
- Use type hints for all function signatures
- Add docstrings to all public functions and classes
- Keep `.env.example` in sync with `config.py`
- Use `logger.error/warning/info` for structured logging
- Handle all exceptions at API layer with proper HTTP status codes

**DON'T:**
- Use `npm`, `node`, `bun` — this is a Python project
- Commit `.env` files or API keys
- Use bare `except:` or empty `except: pass`
- Hardcode configuration values — use `config.py` / env vars
- Use `print()` for logging — use the `logging` module
- Leave docs out of sync with code changes
- Use `os.path` — prefer `pathlib.Path`

## Git Workflow

1. Make changes following style guide
2. `ruff check . --fix && ruff format .` — auto-fix and format
3. `uv run pytest` — run tests
4. `uv run python main.py` — test locally
5. Commit with descriptive message (Chinese or English)
