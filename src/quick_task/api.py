"""Programmatic API for Quick Task.

Provides a clean interface for other Python programs to manage
markdown-based task files without going through the CLI.
"""

from pathlib import Path

from quick_task.discovery import find_task_file
from quick_task.matcher import find_task, find_tasks, all_tasks, AmbiguousMatchError
from quick_task.models import Task, TaskList, TaskFile, TaskStatus
from quick_task.operations import (
    add_task,
    update_status,
    move_task,
    remove_task,
    rename_task,
    link_dependency,
    link_doc,
    set_task_metadata,
    TaskNotFoundError,
    ListNotFoundError,
    CircularDependencyError,
)
from quick_task.parser import parse_file, parse_content
from quick_task.writer import write_file, write_content
from quick_task.checker import check_file, check_content


def load_file(path: str | Path | None = None) -> TaskFile:
    """Load a task file, discovering it automatically if no path given.

    If path is None, walks up from cwd looking for TASKS.md.
    Raises FileNotFoundError if no task file is found.
    """
    if path is not None:
        resolved = Path(path)
        if not resolved.exists():
            raise FileNotFoundError(f"Task file not found: {path}")
        return parse_file(resolved)

    found = find_task_file()
    if found is None:
        raise FileNotFoundError("No TASKS.md found in current or parent directories")
    return parse_file(found)


def get_task(task_file: TaskFile, query: str) -> Task:
    """Find a single task by bookmark or title substring.

    Raises TaskNotFoundError if no match.
    Raises AmbiguousMatchError if multiple matches.
    """
    task = find_task(task_file, query)
    if task is None:
        raise TaskNotFoundError(f"Task not found: {query}")
    return task


def list_tasks(
    task_file: TaskFile,
    *,
    list_name: str | None = None,
    status: TaskStatus | None = None,
    assignee: str | None = None,
    priority: str | None = None,
    flat: bool = False,
) -> list[Task]:
    """List tasks from a task file with optional filtering.

    Args:
        task_file: The parsed task file.
        list_name: Filter to tasks in this list (case-insensitive).
        status: Filter to tasks with this status.
        assignee: Filter to tasks assigned to this person (e.g. ``@builder``).
            Matching is case-insensitive and checks both the exact value and
            a simple containment check so ``@builder`` matches ``@Builder``.
        priority: Filter to tasks with this priority level (``low``,
            ``medium``, ``high``, ``critical``).
        flat: If True, return all tasks flattened (including nested children).
              If False, return only top-level tasks per list.
    """
    tasks: list[Task] = []

    for tl in task_file.lists:
        if list_name and tl.name.lower() != list_name.lower():
            continue
        if flat:
            from quick_task.matcher import collect_tasks
            tasks.extend(collect_tasks(tl.tasks))
        else:
            tasks.extend(tl.tasks)

    if status is not None:
        tasks = [t for t in tasks if t.status == status]

    if assignee is not None:
        needle = assignee.lower()
        tasks = [t for t in tasks if t.assignee is not None and t.assignee.lower() == needle]

    if priority is not None:
        needle = priority.lower()
        tasks = [t for t in tasks if t.priority is not None and t.priority.lower() == needle]

    return tasks


def save(task_file: TaskFile) -> None:
    """Write a task file back to disk."""
    write_file(task_file)


__all__ = [
    # Core loading/saving
    "load_file",
    "save",
    # Query
    "get_task",
    "list_tasks",
    "find_tasks",
    "all_tasks",
    # Mutations
    "add_task",
    "update_status",
    "move_task",
    "remove_task",
    "rename_task",
    "link_dependency",
    "link_doc",
    "set_task_metadata",
    # Parsing (advanced)
    "parse_file",
    "parse_content",
    "write_content",
    # Validation
    "check_file",
    "check_content",
    # Models
    "Task",
    "TaskList",
    "TaskFile",
    "TaskStatus",
    # Exceptions
    "TaskNotFoundError",
    "ListNotFoundError",
    "CircularDependencyError",
    "AmbiguousMatchError",
]
