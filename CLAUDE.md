# CLAUDE.md — Quick Task

## Build & Test

```bash
# Install (editable, with dev dependencies)
pip install -e ".[dev]"

# Run all tests
pytest

# Run specific test file
pytest tests/test_operations.py -v

# Run tests matching a keyword
pytest -k "bookmark"
```

## Project Structure

- `src/quick_task/` — Main package
  - `models.py` — Core dataclasses: `Task`, `TaskList`, `TaskFile`, `TaskStatus` enum
  - `parser.py` — Markdown → data model (regex-based, handles nesting via indent tracking)
  - `writer.py` — Data model → markdown (preserves formatting)
  - `operations.py` — Mutations: add, update_status, move, rename, remove, link, rollup
  - `api.py` — Public API: load_file, get_task, list_tasks, save + re-exports
  - `matcher.py` — Task finding: exact bookmark match or fuzzy title substring
  - `discovery.py` — Walks up from cwd to find TASKS.md
  - `checker.py` — Validates task files (syntax, duplicates, orphaned metadata)
  - `cli.py` — Click CLI (entry point: `qt`)
- `tests/` — pytest tests with fixtures in `tests/fixtures/`
- `demo/TASKS.md` — Example task file

## Architecture

Layered design — each layer depends only on layers below:

```
CLI (cli.py)
  ↓
API (api.py)
  ↓
Operations (operations.py)
  ↓
Parser/Writer (parser.py, writer.py) + Matcher (matcher.py)
  ↓
Models (models.py)
```

## Conventions

- Python 3.11+, type hints throughout
- CLI uses Click with Rich for terminal formatting
- Task matching: `#bookmark` for exact match, otherwise case-insensitive title substring
- `AmbiguousMatchError` raised when multiple tasks match a query
- `update_status` cascades to children (e.g., `done` marks all subtasks done)
- `rollup_if_children_done` auto-completes parent when all children are done
- Metadata stored as indented `key: value` lines under tasks

## Key Types

```python
TaskStatus: Enum  — TODO(" "), IN_PROGRESS("~"), DONE("x"), CANCELLED("-"), BLOCKED("?"), DEFERRED(">")
Task: dataclass   — title, status, bookmark, metadata dict, children list
TaskList: dataclass — name, tasks list, bookmark
TaskFile: dataclass — path, lists of TaskList
```

## Dependencies

- `click` — CLI framework
- `rich` — Colored terminal output
- `pytest` / `pytest-cov` — Testing (dev only)
