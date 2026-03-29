# Design: Agent-Oriented Metadata Fields (`qt-metadata`)

## Overview

Add first-class metadata fields (`assignee`, `priority`, `created`, `updated`) to quick-task tasks, with CLI flags to set them on `qt add`, and filter support in `qt list`.

These fields live in the task's existing `metadata: dict[str, str]` (see `models.py:Task`) -- no schema changes to the `Task` model are required. The parser, writer, and checker already handle arbitrary metadata key/value pairs.

---

## Current State (as of last builder run)

The codebase is **substantially implemented**. The following already exists:

| Component | Status |
|-----------|--------|
| `models.py` -- `METADATA_*` constants, `PRIORITY_LEVELS`, typed property accessors on `Task` | Done |
| `operations.py` -- `add_task(assignee, priority, stamp_created)`, `_now_iso()`, `set_task_metadata()` | Done |
| `api.py` -- `list_tasks(assignee, priority)` filters, `set_task_metadata` in `__all__` | Done |
| `src/quick_task/metadata.py` -- standalone constants/helpers module | Missing |
| CLI `add` -- `--assignee`, `--priority` flags | Missing |
| CLI `list` -- `--assignee`, `--priority` filter flags | Missing |
| CLI `list --json` -- `metadata` field in JSON output | Missing |
| `api.py` -- `metadata.py` constants in `__all__` | Missing (module doesn't exist yet) |
| Tests -- `test_metadata.py`, metadata coverage in ops/cli/api tests | Missing |

### Important naming note

The design doc specified `set_metadata()` but the builder implemented it as `set_task_metadata()` in `operations.py` and exposed it as `set_task_metadata` in `api.py`. **Keep this name** -- it is already in the codebase and changing it would break the `__all__` export.

---

## What Needs to Be Built

### 1. `src/quick_task/metadata.py` -- Create

A thin module that re-exports the constants and helpers already defined in `models.py` and `operations.py`, providing the single import point specified by the design.

```python
"""Metadata field constants and helpers for Quick Task."""

# Re-export from models to avoid duplication
from quick_task.models import (
    METADATA_ASSIGNEE as FIELD_ASSIGNEE,
    METADATA_PRIORITY as FIELD_PRIORITY,
    METADATA_CREATED  as FIELD_CREATED,
    METADATA_UPDATED  as FIELD_UPDATED,
    PRIORITY_LEVELS   as VALID_PRIORITIES,
)


def validate_priority(value: str) -> str:
    """Lowercase and validate. Raises ValueError on bad input."""
    lowered = value.lower()
    if lowered not in VALID_PRIORITIES:
        raise ValueError(
            f"Invalid priority {value!r}. Must be one of: {', '.join(VALID_PRIORITIES)}"
        )
    return lowered


def now_iso() -> str:
    """Return current UTC time as ISO-8601 string (no microseconds)."""
    import datetime
    return datetime.datetime.now(tz=datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
```

**Rationale**: `operations.py` already has `_now_iso()` (private) and inline priority validation. The public `metadata.py` exposes testable, monkeypatchable versions. `operations.py` does NOT need to change its internal `_now_iso()` -- both can coexist. `metadata.py` is additive and does not alter existing behaviour.

---

### 2. `src/quick_task/cli.py` -- Modify

#### `qt add` -- add `--assignee` and `--priority`

```python
@main.command("add")
@click.argument("title")
@click.option("--list", "-l", "list_name", help="Target list name")
@click.option("--parent", "-p", "parent_query", help="Parent task (creates subtask)")
@click.option("--assignee", help="Assign to an agent or person (e.g. @builder)")
@click.option(
    "--priority",
    type=click.Choice(["low", "medium", "high", "critical"], case_sensitive=False),
    help="Task priority",
)
@click.pass_context
def add(ctx, title, list_name, parent_query, assignee, priority):
    """Add a new task."""
    task_file = _load(ctx)
    try:
        task = op_add_task(
            task_file, title,
            list_name=list_name,
            parent_query=parent_query,
            assignee=assignee,
            priority=priority,
        )
        save(task_file)
        console.print(f"[green]Added:[/green] {task.title}")
    except Exception as e:
        console.print(f"[red]Error:[/red] {e}")
        raise SystemExit(1)
```

#### `qt list` -- add `--assignee` and `--priority` filters

Add options after `--verbose`:

```python
@click.option("--assignee", help="Filter by assignee (case-insensitive exact match)")
@click.option("--priority", help="Filter by priority (low/medium/high/critical)")
```

Add filter logic after the existing status filter:

```python
if assignee:
    needle = assignee.lower()
    tasks = [t for t in tasks if t["task"].metadata.get("assignee", "").lower() == needle]
if priority:
    needle = priority.lower()
    tasks = [t for t in tasks if t["task"].metadata.get("priority", "").lower() == needle]
```

#### `qt list --json` -- add `metadata` to output

Change the JSON output dict to include `metadata`:

```python
output = [
    {
        "title": t["task"].title,
        "status": t["status"].name.lower(),
        "list": t["list"],
        "bookmark": t["task"].bookmark,
        "metadata": dict(t["task"].metadata),  # ADD
    }
    for t in tasks
]
```

---

### 3. `src/quick_task/api.py` -- Modify (minor)

Add the `metadata.py` module symbols to imports and `__all__` once `metadata.py` exists:

```python
from quick_task.metadata import (
    FIELD_ASSIGNEE,
    FIELD_PRIORITY,
    FIELD_CREATED,
    FIELD_UPDATED,
    VALID_PRIORITIES,
    validate_priority,
    now_iso,
)
```

Append to `__all__`:
```python
"FIELD_ASSIGNEE", "FIELD_PRIORITY", "FIELD_CREATED", "FIELD_UPDATED",
"VALID_PRIORITIES", "validate_priority", "now_iso",
```

No changes needed to `list_tasks()` -- it already filters by `assignee` and `priority` correctly.

---

## File Paths Summary

| Path | Action |
|------|--------|
| `../quick-task/src/quick_task/metadata.py` | Create |
| `../quick-task/src/quick_task/cli.py` | Modify -- `add` flags + `list` filters + JSON metadata |
| `../quick-task/src/quick_task/api.py` | Modify -- expose `metadata.py` symbols in `__all__` |
| `../quick-task/tests/test_metadata.py` | Create |
| `../quick-task/tests/test_operations.py` | Modify -- metadata test cases |
| `../quick-task/tests/test_cli.py` | Modify -- new CLI flag tests |
| `../quick-task/tests/test_api.py` | Modify -- metadata filter tests |

---

## Key Design Decisions

1. **`metadata.py` re-exports from `models.py` -- no duplication.** `models.py` already owns `METADATA_*` and `PRIORITY_LEVELS`. `metadata.py` aliases them under the names the original design specified (`FIELD_*`, `VALID_PRIORITIES`) and adds public `validate_priority()` and `now_iso()` helpers.

2. **`set_task_metadata()` name preserved.** The builder chose `set_task_metadata` over the design's `set_metadata`. This is already in `__all__` -- do not rename.

3. **`_now_iso()` in `operations.py` stays private.** The public `now_iso()` in `metadata.py` is for external callers and test monkeypatching. Both implementations are identical; no need to consolidate.

4. **CLI `list` filters use `metadata.get()` directly** (not `.assignee` property) for consistency with the existing pattern in `cli.py` where `t["task"].metadata` is accessed for verbose display.

5. **`click.Choice` for `--priority` on `add`.** Provides built-in error message. `operations.add_task()` still validates internally for programmatic callers.

6. **`--priority` on `list` is a plain string option** (not `click.Choice`) -- allows filtering by any string value without restricting valid inputs at the CLI layer.

7. **JSON output gains `metadata` field.** The `show --json` path already includes metadata via `task_to_dict()`. The `list --json` path was missing it; adding it makes the two outputs consistent.

8. **`set_task_metadata()` with no-op behaviour.** If neither `assignee` nor `priority` is given, the function still stamps `updated` (because `stamp_updated=True` by default). Callers wishing to skip the stamp must pass `stamp_updated=False`. This is already implemented.
