# Architecture & Design (ARCH) - news

## 1. Tech Stack
- **Language**: Python 3.14
- **Environment**: Docker / Dev Container
- **Linter/Formatter**: Ruff
- **Schema**: Pydantic

## 2. Directory Structure
```text
.
├── .agents/          # Rules, Skills, Workflows
├── .devcontainer/    # VS Code Environment Configuration
├── docs/             # Documentation (PRD, ARCH)
├── src/              # Source Code
│   ├── core/         # Core logic
│   ├── utils/        # Shared utilities
│   └── main.py       # Entry point
├── config/           # Configuration files
├── data/             # Local data storage
├── scripts/          # Automation scripts
├── tests/            # Test suite
├── Dockerfile        # Docker configuration
└── docker-compose.yml # Docker orchestration
```

## 3. Module Description
- `src/main.py`: Entry point for the application.
- `src/core/`: Main business logic.
- `src/utils/`: Generic utility functions.

---
*Project: news*
