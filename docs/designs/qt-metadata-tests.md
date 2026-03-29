# Test Specification: Agent-Oriented Metadata Fields (`qt-metadata`)

## Overview

This specification covers all tests to be written or extended for the
`qt-metadata` feature. Tests are grouped by the file they live in.

---

## 1. `tests/test_metadata.py` -- **Create**

Unit tests for the new `src/quick_task/metadata.py` module.

### Constants / Re-exports

| Test | Description |
|------|-------------|
| `test_field_constants` | `FIELD_ASSIGNEE == "assignee"`, `FIELD_PRIORITY == "priority"`, `FIELD_CREATED == "created"`, `FIELD_UPDATED == "updated"` |
| `test_valid_priorities_tuple` | `VALID_PRIORITIES == ("low", "medium", "high", "critical")` and is iterable/ordered |

### `validate_priority()`

| Test | Expected behaviour |
|------|-------------------|
| `test_validate_priority_valid_values` | `"low"`, `"medium"`, `"high"`, `"critical"` all return the same string (lowercased) |
| `test_validate_priority_case_insensitive` | `"HIGH"` returns `"high"`, `"Critical"` returns `"critical"` |
| `test_validate_priority_invalid_raises` | `"urgent"`, `""`, `"normal"` each raise `ValueError` with a message containing the bad value |
| `test_validate_priority_error_message_lists_valid` | Error message from an invalid input contains all four valid values |

### `now_iso()`

| Test | Expected behaviour |
|------|-------------------|
| `test_now_iso_format` | Returns a string matching `r"\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z"` |
| `test_now_iso_is_utc` | The returned timestamp is parseable as a UTC datetime (no offset, ends in `Z`) |
| `test_now_iso_no_microseconds` | Returned string does **not** contain a `.` (no fractional seconds) |

### Import surface (smoke)

| Test | Expected behaviour |
|------|-------------------|
| `test_metadata_module_exports` | `from quick_task.metadata import FIELD_ASSIGNEE, FIELD_PRIORITY, FIELD_CREATED, FIELD_UPDATED, VALID_PRIORITIES, validate_priority, now_iso` succeeds without error |

---

## 2. `tests/test_operations.py` -- **Extend**

Add the following test cases to the existing file.

### `add_task()` with metadata

| Test | Expected behaviour |
|------|-------------------|
| `test_add_task_with_assignee` | `add_task(tf, "T", assignee="@builder")` sets `task.assignee == "@builder"` |
| `test_add_task_with_priority` | `add_task(tf, "T", priority="high")` sets `task.priority == "high"` |
| `test_add_task_with_assignee_and_priority` | Both set correctly on returned task |
| `test_add_task_stamps_created_by_default` | `task.created` matches ISO-8601 format and is not None |
| `test_add_task_no_created_when_disabled` | `add_task(tf, "T", stamp_created=False)` sets `task.created` to None |
| `test_add_task_invalid_priority_raises` | `add_task(tf, "T", priority="urgent")` raises `ValueError` |
| `test_add_task_created_is_utc_string` | `task.created` ends with `"Z"` and parses as UTC |

### `set_task_metadata()`

All tests use a `TaskFile` built from a single-task list.

| Test | Expected behaviour |
|------|-------------------|
| `test_set_task_metadata_assignee` | Sets `task.assignee` on found task |
| `test_set_task_metadata_priority` | Sets `task.priority` on found task |
| `test_set_task_metadata_both` | Sets both fields at once |
| `test_set_task_metadata_stamps_updated` | `task.updated` is set (non-None ISO string) when `stamp_updated=True` (default) |
| `test_set_task_metadata_no_stamp` | `task.updated is None` when `stamp_updated=False` |
| `test_set_task_metadata_clear_assignee` | Passing `assignee=""` removes the field (`task.assignee is None`) |
| `test_set_task_metadata_clear_priority` | Passing `priority=""` removes the field (`task.priority is None`) |
| `test_set_task_metadata_none_does_not_change` | Passing `assignee=None` on a task that already has an assignee leaves it unchanged |
| `test_set_task_metadata_invalid_priority_raises` | `priority="extreme"` raises `ValueError` |
| `test_set_task_metadata_task_not_found_raises` | `query="nonexistent"` raises `TaskNotFoundError` |

---

## 3. `tests/test_cli.py` -- **Extend**

Add the following test cases (all use `CliRunner` + `isolated_filesystem`).

### `qt add --assignee` and `--priority`

**Setup**: a minimal `TASKS.md` with one existing task.

| Test | Invocation | Expected behaviour |
|------|------------|-------------------|
| `test_add_with_assignee` | `["add", "New task", "--assignee", "@builder"]` | Exit 0; `TASKS.md` contains `assignee: @builder` |
| `test_add_with_priority` | `["add", "New task", "--priority", "high"]` | Exit 0; `TASKS.md` contains `priority: high` |
| `test_add_with_assignee_and_priority` | `["add", "New task", "--assignee", "@planner", "--priority", "critical"]` | Both metadata lines present in written file |
| `test_add_priority_case_insensitive` | `["add", "New task", "--priority", "HIGH"]` | Exit 0; stored as `priority: high` (Click `case_sensitive=False`) |
| `test_add_invalid_priority_rejected` | `["add", "New task", "--priority", "urgent"]` | Exit non-zero; output contains `"Invalid value"` or `"Error"` (Click Choice rejects it) |
| `test_add_stamps_created` | `["add", "New task"]` | `TASKS.md` contains a `created:` line with ISO-8601 format |

### `qt list --assignee` and `--priority`

**Setup**: a `TASKS.md` with three tasks:
- Task A: `assignee: @builder`, `priority: high`
- Task B: `assignee: @planner`, `priority: low`
- Task C: no assignee, `priority: high`

| Test | Invocation | Expected behaviour |
|------|------------|-------------------|
| `test_list_filter_by_assignee` | `["list", "--assignee", "@builder"]` | Exit 0; `Task A` in output, `Task B` and `Task C` not in output |
| `test_list_filter_by_assignee_case_insensitive` | `["list", "--assignee", "@BUILDER"]` | `Task A` present |
| `test_list_filter_by_priority` | `["list", "--priority", "high"]` | `Task A` and `Task C` in output, `Task B` not in output |
| `test_list_filter_by_assignee_and_priority` | `["list", "--assignee", "@builder", "--priority", "high"]` | Only `Task A` in output |
| `test_list_filter_assignee_no_match` | `["list", "--assignee", "@nobody"]` | Exit 0; empty table body (no tasks) |
| `test_list_filter_priority_no_match` | `["list", "--priority", "critical"]` | Exit 0; empty table body |

### `qt list --json` includes metadata

| Test | Invocation | Expected behaviour |
|------|------------|-------------------|
| `test_list_json_includes_metadata_key` | `["list", "--json"]` | Every object in JSON array has a `"metadata"` key |
| `test_list_json_metadata_values` | File with `assignee: @builder` on a task | That task's JSON object has `metadata["assignee"] == "@builder"` |
| `test_list_json_metadata_empty_dict` | Task with no metadata | `"metadata": {}` in JSON |

---

## 4. `tests/test_api.py` -- **Extend**

Add the following cases to the existing file.

### `list_tasks()` filtering

| Test | Expected behaviour |
|------|-------------------|
| `test_list_tasks_filter_by_assignee` | Only tasks with matching assignee (exact, case-insensitive) returned |
| `test_list_tasks_filter_by_assignee_case_insensitive` | `assignee="@BUILDER"` matches a task with `assignee="@builder"` |
| `test_list_tasks_filter_by_priority` | Only tasks with matching priority returned |
| `test_list_tasks_filter_by_assignee_and_priority` | Intersection: both filters applied |
| `test_list_tasks_filter_no_match_returns_empty` | `assignee="@nobody"` returns empty list (no exception) |
| `test_list_tasks_assignee_filter_excludes_unset` | Tasks without any assignee are excluded when `assignee` filter is specified |
| `test_list_tasks_priority_filter_excludes_unset` | Tasks without any priority are excluded when `priority` filter is specified |

### `set_task_metadata` in `__all__` (smoke)

| Test | Expected behaviour |
|------|-------------------|
| `test_set_task_metadata_in_api_all` | `"set_task_metadata" in quick_task.api.__all__` is `True` |

### `metadata.py` symbols in `__all__` (smoke)

| Test | Expected behaviour |
|------|-------------------|
| `test_metadata_symbols_in_api_all` | Each of `FIELD_ASSIGNEE`, `FIELD_PRIORITY`, `FIELD_CREATED`, `FIELD_UPDATED`, `VALID_PRIORITIES`, `validate_priority`, `now_iso` is present in `quick_task.api.__all__` |
| `test_metadata_symbols_importable_from_api` | `from quick_task.api import FIELD_ASSIGNEE, validate_priority, now_iso` succeeds and values are correct |

---

## Mocking Strategy

### `now_iso()` in `metadata.py`
- Use `monkeypatch.setattr("quick_task.metadata.now_iso", lambda: "2024-01-01T00:00:00Z")` when tests need deterministic timestamps.
- Tests that only check **format** (not value) can call the real function.

### `_now_iso()` in `operations.py`
- For operations tests that check `created` / `updated` values exactly, use `monkeypatch.setattr("quick_task.operations._now_iso", lambda: "2024-01-01T00:00:00Z")`.
- Tests that only assert the field is non-None can skip the monkeypatch.

### CLI tests
- Use `CliRunner(mix_stderr=False)` with `isolated_filesystem()` as the existing tests do.
- No additional mocking required beyond what Click's test runner provides.

---

## Test Fixtures (shared helpers)

```python
# Reusable in test_operations.py and test_api.py
def make_task_file_with_metadata():
    """TaskFile with tasks carrying assignee/priority metadata."""
    from quick_task.models import Task, TaskList, TaskFile, TaskStatus
    return TaskFile(
        path="test.md",
        lists=[
            TaskList(name="Tasks", tasks=[
                Task(
                    title="Task Alpha",
                    status=TaskStatus.TODO,
                    metadata={"assignee": "@builder", "priority": "high"},
                ),
                Task(
                    title="Task Beta",
                    status=TaskStatus.TODO,
                    metadata={"assignee": "@planner", "priority": "low"},
                ),
                Task(
                    title="Task Gamma",
                    status=TaskStatus.TODO,
                    metadata={"priority": "high"},
                ),
            ]),
        ],
    )
```

---

## Edge Cases Checklist

- `validate_priority` with whitespace (e.g. `" high "`) raises `ValueError` (no trimming)
- `add_task` with `priority="LOW"` (all-caps) raises `ValueError` in operations.py (validates against `PRIORITY_LEVELS` without lowercasing); the CLI avoids this by using `click.Choice(case_sensitive=False)` which normalises to lowercase before calling the operation
- `set_task_metadata` with `assignee=""` and `stamp_updated=False`: field cleared, `updated` unchanged
- `qt list --assignee @nobody` on an empty file: exits 0, no crash
- `qt list --json` on a file where some tasks have metadata and some do not: all objects have `"metadata"` key (empty dict for those without)
- JSON round-trip: add task via CLI with `--assignee` and `--priority`, then `list --json`: values preserved exactly
