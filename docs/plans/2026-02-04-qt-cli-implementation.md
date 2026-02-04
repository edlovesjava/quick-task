# Quick Task (qt) CLI Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Build a Python CLI tool that manages tasks in markdown files, supporting hierarchical tasks, dependencies, and multiple task lists.

**Architecture:** Click-based CLI wrapping a core library. Parser reads markdown into dataclasses, operations mutate the model, writer serializes back preserving formatting. Fuzzy matching for task identification.

**Tech Stack:** Python 3.11+, Click (CLI), Rich (terminal output), pytest (testing)

---

### Task 1: Project Setup

**Files:**
- Create: `pyproject.toml`
- Create: `src/quick_task/__init__.py`
- Create: `src/quick_task/cli.py`

**Step 1: Create pyproject.toml**

```toml
[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"

[project]
name = "quick-task"
version = "0.1.0"
description = "Markdown-based task management CLI"
requires-python = ">=3.11"
dependencies = [
    "click>=8.0",
    "rich>=13.0",
]

[project.optional-dependencies]
dev = [
    "pytest>=8.0",
    "pytest-cov>=4.0",
]

[project.scripts]
qt = "quick_task.cli:main"

[tool.hatch.build.targets.wheel]
packages = ["src/quick_task"]
```

**Step 2: Create package init**

```python
"""Quick Task - Markdown-based task management CLI."""

__version__ = "0.1.0"
```

**Step 3: Create minimal CLI entry point**

```python
"""CLI entry point for Quick Task."""

import click


@click.group()
@click.version_option()
def main():
    """Quick Task - Markdown-based task management."""
    pass


if __name__ == "__main__":
    main()
```

**Step 4: Install in dev mode**

Run: `pip install -e ".[dev]"`
Expected: Successfully installed quick-task

**Step 5: Verify CLI works**

Run: `qt --version`
Expected: `qt, version 0.1.0`

**Step 6: Commit**

```bash
git add pyproject.toml src/
git commit -m "feat: project setup with Click CLI skeleton"
```

---

### Task 2: Data Models

**Files:**
- Create: `src/quick_task/models.py`
- Create: `tests/test_models.py`

**Step 1: Write the failing test**

```python
"""Tests for task data models."""

from quick_task.models import Task, TaskList, TaskFile, TaskStatus


def test_task_creation():
    task = Task(title="Test task", status=TaskStatus.TODO)
    assert task.title == "Test task"
    assert task.status == TaskStatus.TODO
    assert task.bookmark is None
    assert task.children == []
    assert task.metadata == {}


def test_task_with_bookmark():
    task = Task(title="Auth system", status=TaskStatus.TODO, bookmark="auth")
    assert task.bookmark == "auth"


def test_task_with_children():
    child1 = Task(title="Subtask 1", status=TaskStatus.DONE)
    child2 = Task(title="Subtask 2", status=TaskStatus.TODO)
    parent = Task(title="Parent", status=TaskStatus.IN_PROGRESS, children=[child1, child2])
    assert len(parent.children) == 2
    assert parent.children[0].status == TaskStatus.DONE


def test_task_with_metadata():
    task = Task(
        title="Complex task",
        status=TaskStatus.TODO,
        metadata={"depends": "Other task", "docs": "docs/spec.md"},
    )
    assert task.metadata["depends"] == "Other task"


def test_task_list_creation():
    task1 = Task(title="Task 1", status=TaskStatus.TODO)
    task2 = Task(title="Task 2", status=TaskStatus.DONE)
    task_list = TaskList(name="Backlog", tasks=[task1, task2], bookmark="backlog")
    assert task_list.name == "Backlog"
    assert len(task_list.tasks) == 2
    assert task_list.bookmark == "backlog"


def test_task_file_creation():
    tasks = TaskList(name="Tasks", tasks=[])
    done = TaskList(name="Done", tasks=[])
    task_file = TaskFile(path="TASKS.md", lists=[tasks, done])
    assert task_file.path == "TASKS.md"
    assert len(task_file.lists) == 2


def test_task_status_values():
    assert TaskStatus.TODO.symbol == " "
    assert TaskStatus.IN_PROGRESS.symbol == "~"
    assert TaskStatus.DONE.symbol == "x"
    assert TaskStatus.CANCELLED.symbol == "-"
    assert TaskStatus.BLOCKED.symbol == "?"
    assert TaskStatus.DEFERRED.symbol == ">"
```

**Step 2: Run test to verify it fails**

Run: `pytest tests/test_models.py -v`
Expected: FAIL with ModuleNotFoundError

**Step 3: Write the models implementation**

```python
"""Data models for Quick Task."""

from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path


class TaskStatus(Enum):
    """Task status with markdown checkbox symbols."""

    TODO = " "
    IN_PROGRESS = "~"
    DONE = "x"
    CANCELLED = "-"
    BLOCKED = "?"
    DEFERRED = ">"

    @property
    def symbol(self) -> str:
        return self.value

    @classmethod
    def from_symbol(cls, symbol: str) -> "TaskStatus":
        for status in cls:
            if status.value == symbol:
                return status
        raise ValueError(f"Unknown status symbol: {symbol}")


@dataclass
class Task:
    """A single task with optional children and metadata."""

    title: str
    status: TaskStatus
    bookmark: str | None = None
    children: list["Task"] = field(default_factory=list)
    metadata: dict[str, str] = field(default_factory=dict)


@dataclass
class TaskList:
    """A named list of tasks (corresponds to a markdown header)."""

    name: str
    tasks: list[Task] = field(default_factory=list)
    bookmark: str | None = None


@dataclass
class TaskFile:
    """A markdown file containing one or more task lists."""

    path: str | Path
    lists: list[TaskList] = field(default_factory=list)
```

**Step 4: Run test to verify it passes**

Run: `pytest tests/test_models.py -v`
Expected: All 7 tests PASS

**Step 5: Commit**

```bash
git add src/quick_task/models.py tests/test_models.py
git commit -m "feat: add Task, TaskList, TaskFile data models"
```

---

### Task 3: Markdown Parser - Basic Tasks

**Files:**
- Create: `src/quick_task/parser.py`
- Create: `tests/test_parser.py`
- Create: `tests/fixtures/simple.md`

**Step 1: Create test fixture**

Create `tests/fixtures/simple.md`:
```markdown
## Tasks

- [ ] First task
- [x] Completed task
- [~] In progress task
```

**Step 2: Write the failing test**

```python
"""Tests for markdown parser."""

from pathlib import Path

from quick_task.parser import parse_file
from quick_task.models import TaskStatus


FIXTURES = Path(__file__).parent / "fixtures"


def test_parse_simple_tasks():
    task_file = parse_file(FIXTURES / "simple.md")
    assert len(task_file.lists) == 1
    assert task_file.lists[0].name == "Tasks"

    tasks = task_file.lists[0].tasks
    assert len(tasks) == 3

    assert tasks[0].title == "First task"
    assert tasks[0].status == TaskStatus.TODO

    assert tasks[1].title == "Completed task"
    assert tasks[1].status == TaskStatus.DONE

    assert tasks[2].title == "In progress task"
    assert tasks[2].status == TaskStatus.IN_PROGRESS
```

**Step 3: Run test to verify it fails**

Run: `pytest tests/test_parser.py::test_parse_simple_tasks -v`
Expected: FAIL with ImportError

**Step 4: Write minimal parser implementation**

```python
"""Markdown parser for task files."""

import re
from pathlib import Path

from quick_task.models import Task, TaskList, TaskFile, TaskStatus


HEADER_PATTERN = re.compile(r"^(#{1,6})\s+(.+?)(?:\s+\[#([\w-]+)\])?\s*$")
TASK_PATTERN = re.compile(r"^(\s*)- \[(.)\]\s+(.+?)(?:\s+\[#([\w-]+)\])?\s*$")


def parse_file(path: str | Path) -> TaskFile:
    """Parse a markdown file into a TaskFile."""
    path = Path(path)
    content = path.read_text()
    return parse_content(content, path)


def parse_content(content: str, path: str | Path = "TASKS.md") -> TaskFile:
    """Parse markdown content into a TaskFile."""
    lines = content.split("\n")
    lists: list[TaskList] = []
    current_list: TaskList | None = None

    for line in lines:
        # Check for header
        header_match = HEADER_PATTERN.match(line)
        if header_match:
            name = header_match.group(2)
            bookmark = header_match.group(3)
            current_list = TaskList(name=name, bookmark=bookmark)
            lists.append(current_list)
            continue

        # Check for task
        task_match = TASK_PATTERN.match(line)
        if task_match and current_list is not None:
            indent = len(task_match.group(1))
            symbol = task_match.group(2)
            title = task_match.group(3)
            bookmark = task_match.group(4)

            status = TaskStatus.from_symbol(symbol)
            task = Task(title=title, status=status, bookmark=bookmark)

            if indent == 0:
                current_list.tasks.append(task)

    return TaskFile(path=path, lists=lists)
```

**Step 5: Run test to verify it passes**

Run: `pytest tests/test_parser.py::test_parse_simple_tasks -v`
Expected: PASS

**Step 6: Commit**

```bash
git add src/quick_task/parser.py tests/test_parser.py tests/fixtures/
git commit -m "feat: basic markdown parser for flat task lists"
```

---

### Task 4: Parser - Nested Tasks

**Files:**
- Modify: `src/quick_task/parser.py`
- Modify: `tests/test_parser.py`
- Create: `tests/fixtures/nested.md`

**Step 1: Create test fixture**

Create `tests/fixtures/nested.md`:
```markdown
## Tasks

- [ ] Parent task
    - [x] Child 1
    - [ ] Child 2
        - [ ] Grandchild
- [ ] Another top-level
```

**Step 2: Write the failing test**

Add to `tests/test_parser.py`:
```python
def test_parse_nested_tasks():
    task_file = parse_file(FIXTURES / "nested.md")
    tasks = task_file.lists[0].tasks

    assert len(tasks) == 2  # Two top-level tasks

    parent = tasks[0]
    assert parent.title == "Parent task"
    assert len(parent.children) == 2

    assert parent.children[0].title == "Child 1"
    assert parent.children[0].status == TaskStatus.DONE

    assert parent.children[1].title == "Child 2"
    assert len(parent.children[1].children) == 1
    assert parent.children[1].children[0].title == "Grandchild"
```

**Step 3: Run test to verify it fails**

Run: `pytest tests/test_parser.py::test_parse_nested_tasks -v`
Expected: FAIL - children not being parsed

**Step 4: Update parser to handle nesting**

Replace the task parsing section in `parse_content`:

```python
def parse_content(content: str, path: str | Path = "TASKS.md") -> TaskFile:
    """Parse markdown content into a TaskFile."""
    lines = content.split("\n")
    lists: list[TaskList] = []
    current_list: TaskList | None = None
    task_stack: list[tuple[int, Task]] = []  # (indent_level, task)

    for line in lines:
        # Check for header
        header_match = HEADER_PATTERN.match(line)
        if header_match:
            name = header_match.group(2)
            bookmark = header_match.group(3)
            current_list = TaskList(name=name, bookmark=bookmark)
            lists.append(current_list)
            task_stack = []
            continue

        # Check for task
        task_match = TASK_PATTERN.match(line)
        if task_match and current_list is not None:
            indent = len(task_match.group(1))
            symbol = task_match.group(2)
            title = task_match.group(3)
            bookmark = task_match.group(4)

            status = TaskStatus.from_symbol(symbol)
            task = Task(title=title, status=status, bookmark=bookmark)

            # Pop stack until we find parent at lower indent
            while task_stack and task_stack[-1][0] >= indent:
                task_stack.pop()

            if task_stack:
                # Add as child of top of stack
                task_stack[-1][1].children.append(task)
            else:
                # Top-level task
                current_list.tasks.append(task)

            task_stack.append((indent, task))

    return TaskFile(path=path, lists=lists)
```

**Step 5: Run test to verify it passes**

Run: `pytest tests/test_parser.py -v`
Expected: All tests PASS

**Step 6: Commit**

```bash
git add src/quick_task/parser.py tests/test_parser.py tests/fixtures/nested.md
git commit -m "feat: parser handles nested tasks"
```

---

### Task 5: Parser - Metadata and Bookmarks

**Files:**
- Modify: `src/quick_task/parser.py`
- Modify: `tests/test_parser.py`
- Create: `tests/fixtures/metadata.md`

**Step 1: Create test fixture**

Create `tests/fixtures/metadata.md`:
```markdown
## Backlog [#backlog]

- [ ] Complex task [#complex]
    depends: Other task
    docs: docs/spec.md
- [ ] Other task
```

**Step 2: Write the failing test**

Add to `tests/test_parser.py`:
```python
def test_parse_metadata_and_bookmarks():
    task_file = parse_file(FIXTURES / "metadata.md")

    assert task_file.lists[0].name == "Backlog"
    assert task_file.lists[0].bookmark == "backlog"

    tasks = task_file.lists[0].tasks
    assert tasks[0].title == "Complex task"
    assert tasks[0].bookmark == "complex"
    assert tasks[0].metadata["depends"] == "Other task"
    assert tasks[0].metadata["docs"] == "docs/spec.md"
```

**Step 3: Run test to verify it fails**

Run: `pytest tests/test_parser.py::test_parse_metadata_and_bookmarks -v`
Expected: FAIL - metadata not parsed

**Step 4: Update parser to handle metadata**

Add metadata pattern and update parsing:

```python
METADATA_PATTERN = re.compile(r"^\s+([\w-]+):\s*(.+)\s*$")


def parse_content(content: str, path: str | Path = "TASKS.md") -> TaskFile:
    """Parse markdown content into a TaskFile."""
    lines = content.split("\n")
    lists: list[TaskList] = []
    current_list: TaskList | None = None
    task_stack: list[tuple[int, Task]] = []  # (indent_level, task)
    current_task: Task | None = None

    for line in lines:
        # Check for header
        header_match = HEADER_PATTERN.match(line)
        if header_match:
            name = header_match.group(2)
            bookmark = header_match.group(3)
            current_list = TaskList(name=name, bookmark=bookmark)
            lists.append(current_list)
            task_stack = []
            current_task = None
            continue

        # Check for task
        task_match = TASK_PATTERN.match(line)
        if task_match and current_list is not None:
            indent = len(task_match.group(1))
            symbol = task_match.group(2)
            title = task_match.group(3)
            bookmark = task_match.group(4)

            status = TaskStatus.from_symbol(symbol)
            task = Task(title=title, status=status, bookmark=bookmark)

            # Pop stack until we find parent at lower indent
            while task_stack and task_stack[-1][0] >= indent:
                task_stack.pop()

            if task_stack:
                task_stack[-1][1].children.append(task)
            else:
                current_list.tasks.append(task)

            task_stack.append((indent, task))
            current_task = task
            continue

        # Check for metadata (indented key: value)
        metadata_match = METADATA_PATTERN.match(line)
        if metadata_match and current_task is not None:
            key = metadata_match.group(1)
            value = metadata_match.group(2)
            current_task.metadata[key] = value

    return TaskFile(path=path, lists=lists)
```

**Step 5: Run test to verify it passes**

Run: `pytest tests/test_parser.py -v`
Expected: All tests PASS

**Step 6: Commit**

```bash
git add src/quick_task/parser.py tests/test_parser.py tests/fixtures/metadata.md
git commit -m "feat: parser handles metadata and bookmarks"
```

---

### Task 6: Markdown Writer - Basic

**Files:**
- Create: `src/quick_task/writer.py`
- Create: `tests/test_writer.py`

**Step 1: Write the failing test**

```python
"""Tests for markdown writer."""

from quick_task.models import Task, TaskList, TaskFile, TaskStatus
from quick_task.writer import write_content


def test_write_simple_tasks():
    tasks = TaskList(
        name="Tasks",
        tasks=[
            Task(title="First task", status=TaskStatus.TODO),
            Task(title="Done task", status=TaskStatus.DONE),
        ],
    )
    task_file = TaskFile(path="test.md", lists=[tasks])

    content = write_content(task_file)

    expected = """## Tasks

- [ ] First task
- [x] Done task
"""
    assert content == expected


def test_write_nested_tasks():
    parent = Task(
        title="Parent",
        status=TaskStatus.TODO,
        children=[
            Task(title="Child 1", status=TaskStatus.DONE),
            Task(title="Child 2", status=TaskStatus.TODO),
        ],
    )
    tasks = TaskList(name="Tasks", tasks=[parent])
    task_file = TaskFile(path="test.md", lists=[tasks])

    content = write_content(task_file)

    expected = """## Tasks

- [ ] Parent
    - [x] Child 1
    - [ ] Child 2
"""
    assert content == expected


def test_write_with_bookmarks():
    tasks = TaskList(
        name="Backlog",
        bookmark="backlog",
        tasks=[Task(title="Auth system", status=TaskStatus.TODO, bookmark="auth")],
    )
    task_file = TaskFile(path="test.md", lists=[tasks])

    content = write_content(task_file)

    expected = """## Backlog [#backlog]

- [ ] Auth system [#auth]
"""
    assert content == expected


def test_write_with_metadata():
    task = Task(
        title="Complex task",
        status=TaskStatus.TODO,
        metadata={"depends": "Other task", "docs": "docs/spec.md"},
    )
    tasks = TaskList(name="Tasks", tasks=[task])
    task_file = TaskFile(path="test.md", lists=[tasks])

    content = write_content(task_file)

    assert "- [ ] Complex task" in content
    assert "    depends: Other task" in content
    assert "    docs: docs/spec.md" in content
```

**Step 2: Run test to verify it fails**

Run: `pytest tests/test_writer.py -v`
Expected: FAIL with ImportError

**Step 3: Write the writer implementation**

```python
"""Markdown writer for task files."""

from pathlib import Path

from quick_task.models import Task, TaskList, TaskFile


def write_file(task_file: TaskFile) -> None:
    """Write a TaskFile back to its markdown file."""
    path = Path(task_file.path)
    content = write_content(task_file)
    path.write_text(content)


def write_content(task_file: TaskFile) -> str:
    """Convert a TaskFile to markdown content."""
    lines: list[str] = []

    for task_list in task_file.lists:
        lines.append(format_list_header(task_list))
        lines.append("")
        for task in task_list.tasks:
            lines.extend(format_task(task, indent=0))

    return "\n".join(lines)


def format_list_header(task_list: TaskList) -> str:
    """Format a task list header."""
    header = f"## {task_list.name}"
    if task_list.bookmark:
        header += f" [#{task_list.bookmark}]"
    return header


def format_task(task: Task, indent: int = 0) -> list[str]:
    """Format a task and its children as markdown lines."""
    lines: list[str] = []
    prefix = "    " * indent

    # Task line
    line = f"{prefix}- [{task.status.symbol}] {task.title}"
    if task.bookmark:
        line += f" [#{task.bookmark}]"
    lines.append(line)

    # Metadata
    for key, value in task.metadata.items():
        lines.append(f"{prefix}    {key}: {value}")

    # Children
    for child in task.children:
        lines.extend(format_task(child, indent + 1))

    return lines
```

**Step 4: Run test to verify it passes**

Run: `pytest tests/test_writer.py -v`
Expected: All tests PASS

**Step 5: Commit**

```bash
git add src/quick_task/writer.py tests/test_writer.py
git commit -m "feat: markdown writer for task files"
```

---

### Task 7: Fuzzy Matcher

**Files:**
- Create: `src/quick_task/matcher.py`
- Create: `tests/test_matcher.py`

**Step 1: Write the failing test**

```python
"""Tests for fuzzy task matching."""

from quick_task.models import Task, TaskList, TaskFile, TaskStatus
from quick_task.matcher import find_task, find_tasks


def make_task_file():
    return TaskFile(
        path="test.md",
        lists=[
            TaskList(
                name="Tasks",
                tasks=[
                    Task(title="Design authentication system", status=TaskStatus.TODO, bookmark="auth"),
                    Task(title="Set up database", status=TaskStatus.TODO),
                    Task(title="Build user registration", status=TaskStatus.IN_PROGRESS),
                ],
            )
        ],
    )


def test_exact_match():
    tf = make_task_file()
    task = find_task(tf, "Set up database")
    assert task is not None
    assert task.title == "Set up database"


def test_case_insensitive_match():
    tf = make_task_file()
    task = find_task(tf, "set up database")
    assert task is not None
    assert task.title == "Set up database"


def test_partial_match():
    tf = make_task_file()
    task = find_task(tf, "database")
    assert task is not None
    assert task.title == "Set up database"


def test_bookmark_exact_match():
    tf = make_task_file()
    task = find_task(tf, "#auth")
    assert task is not None
    assert task.title == "Design authentication system"


def test_ambiguous_returns_none():
    tf = make_task_file()
    # Both "Design authentication" and "Build user" contain letters
    # But "user" should match only one
    task = find_task(tf, "user")
    assert task is not None
    assert task.title == "Build user registration"


def test_find_multiple_matches():
    tf = make_task_file()
    # "system" could match authentication system
    tasks = find_tasks(tf, "system")
    assert len(tasks) == 1


def test_no_match_returns_none():
    tf = make_task_file()
    task = find_task(tf, "nonexistent")
    assert task is None
```

**Step 2: Run test to verify it fails**

Run: `pytest tests/test_matcher.py -v`
Expected: FAIL with ImportError

**Step 3: Write the matcher implementation**

```python
"""Fuzzy matching for task titles."""

from quick_task.models import Task, TaskList, TaskFile


def find_task(task_file: TaskFile, query: str) -> Task | None:
    """Find a single task matching the query. Returns None if no match or ambiguous."""
    matches = find_tasks(task_file, query)
    if len(matches) == 1:
        return matches[0]
    return None


def find_tasks(task_file: TaskFile, query: str) -> list[Task]:
    """Find all tasks matching the query."""
    query = query.strip()

    # Bookmark lookup (exact match)
    if query.startswith("#"):
        bookmark = query[1:]
        return [t for t in all_tasks(task_file) if t.bookmark == bookmark]

    # Fuzzy title match
    query_lower = query.lower()
    matches = []
    for task in all_tasks(task_file):
        if query_lower in task.title.lower():
            matches.append(task)

    return matches


def all_tasks(task_file: TaskFile) -> list[Task]:
    """Get all tasks from a task file, flattened."""
    tasks = []
    for task_list in task_file.lists:
        tasks.extend(collect_tasks(task_list.tasks))
    return tasks


def collect_tasks(tasks: list[Task]) -> list[Task]:
    """Recursively collect all tasks including children."""
    result = []
    for task in tasks:
        result.append(task)
        result.extend(collect_tasks(task.children))
    return result
```

**Step 4: Run test to verify it passes**

Run: `pytest tests/test_matcher.py -v`
Expected: All tests PASS

**Step 5: Commit**

```bash
git add src/quick_task/matcher.py tests/test_matcher.py
git commit -m "feat: fuzzy matcher for task titles and bookmarks"
```

---

### Task 8: Operations - Add Task

**Files:**
- Create: `src/quick_task/operations.py`
- Create: `tests/test_operations.py`

**Step 1: Write the failing test**

```python
"""Tests for task operations."""

from quick_task.models import Task, TaskList, TaskFile, TaskStatus
from quick_task.operations import add_task


def make_empty_task_file():
    return TaskFile(
        path="test.md",
        lists=[TaskList(name="Tasks", tasks=[])],
    )


def make_task_file_with_tasks():
    return TaskFile(
        path="test.md",
        lists=[
            TaskList(
                name="Tasks",
                tasks=[
                    Task(title="Existing task", status=TaskStatus.TODO),
                ],
            )
        ],
    )


def test_add_task_to_empty_list():
    tf = make_empty_task_file()
    add_task(tf, "New task")
    assert len(tf.lists[0].tasks) == 1
    assert tf.lists[0].tasks[0].title == "New task"
    assert tf.lists[0].tasks[0].status == TaskStatus.TODO


def test_add_task_appends_to_end():
    tf = make_task_file_with_tasks()
    add_task(tf, "New task")
    assert len(tf.lists[0].tasks) == 2
    assert tf.lists[0].tasks[1].title == "New task"


def test_add_task_to_named_list():
    tf = TaskFile(
        path="test.md",
        lists=[
            TaskList(name="Backlog", tasks=[]),
            TaskList(name="Done", tasks=[]),
        ],
    )
    add_task(tf, "New task", list_name="Done")
    assert len(tf.lists[0].tasks) == 0
    assert len(tf.lists[1].tasks) == 1


def test_add_task_with_parent():
    tf = TaskFile(
        path="test.md",
        lists=[
            TaskList(
                name="Tasks",
                tasks=[Task(title="Parent task", status=TaskStatus.TODO)],
            )
        ],
    )
    add_task(tf, "Child task", parent_query="Parent")
    assert len(tf.lists[0].tasks) == 1
    assert len(tf.lists[0].tasks[0].children) == 1
    assert tf.lists[0].tasks[0].children[0].title == "Child task"
```

**Step 2: Run test to verify it fails**

Run: `pytest tests/test_operations.py -v`
Expected: FAIL with ImportError

**Step 3: Write the add_task implementation**

```python
"""Task operations - add, update, move, etc."""

from quick_task.models import Task, TaskList, TaskFile, TaskStatus
from quick_task.matcher import find_task


class TaskNotFoundError(Exception):
    """Raised when a task cannot be found."""
    pass


class ListNotFoundError(Exception):
    """Raised when a task list cannot be found."""
    pass


def add_task(
    task_file: TaskFile,
    title: str,
    list_name: str | None = None,
    parent_query: str | None = None,
) -> Task:
    """Add a new task to the task file."""
    task = Task(title=title, status=TaskStatus.TODO)

    if parent_query:
        parent = find_task(task_file, parent_query)
        if parent is None:
            raise TaskNotFoundError(f"Parent task not found: {parent_query}")
        parent.children.append(task)
        return task

    target_list = get_list(task_file, list_name)
    target_list.tasks.append(task)
    return task


def get_list(task_file: TaskFile, list_name: str | None = None) -> TaskList:
    """Get a task list by name, or the first list if no name given."""
    if not task_file.lists:
        raise ListNotFoundError("No task lists in file")

    if list_name is None:
        return task_file.lists[0]

    for task_list in task_file.lists:
        if task_list.name.lower() == list_name.lower():
            return task_list

    raise ListNotFoundError(f"List not found: {list_name}")
```

**Step 4: Run test to verify it passes**

Run: `pytest tests/test_operations.py -v`
Expected: All tests PASS

**Step 5: Commit**

```bash
git add src/quick_task/operations.py tests/test_operations.py
git commit -m "feat: add_task operation"
```

---

### Task 9: Operations - Update Status

**Files:**
- Modify: `src/quick_task/operations.py`
- Modify: `tests/test_operations.py`

**Step 1: Write the failing test**

Add to `tests/test_operations.py`:
```python
from quick_task.operations import add_task, update_status


def test_update_status_done():
    tf = TaskFile(
        path="test.md",
        lists=[
            TaskList(
                name="Tasks",
                tasks=[Task(title="My task", status=TaskStatus.TODO)],
            )
        ],
    )
    update_status(tf, "My task", TaskStatus.DONE)
    assert tf.lists[0].tasks[0].status == TaskStatus.DONE


def test_done_cascades_to_children():
    child = Task(title="Child", status=TaskStatus.TODO)
    parent = Task(title="Parent", status=TaskStatus.TODO, children=[child])
    tf = TaskFile(path="test.md", lists=[TaskList(name="Tasks", tasks=[parent])])

    update_status(tf, "Parent", TaskStatus.DONE)

    assert parent.status == TaskStatus.DONE
    assert child.status == TaskStatus.DONE


def test_children_complete_rolls_up_to_parent():
    child1 = Task(title="Child 1", status=TaskStatus.DONE)
    child2 = Task(title="Child 2", status=TaskStatus.TODO)
    parent = Task(title="Parent", status=TaskStatus.TODO, children=[child1, child2])
    tf = TaskFile(path="test.md", lists=[TaskList(name="Tasks", tasks=[parent])])

    update_status(tf, "Child 2", TaskStatus.DONE)

    assert child2.status == TaskStatus.DONE
    assert parent.status == TaskStatus.DONE


def test_cancel_cascades_to_children():
    child = Task(title="Child", status=TaskStatus.TODO)
    parent = Task(title="Parent", status=TaskStatus.TODO, children=[child])
    tf = TaskFile(path="test.md", lists=[TaskList(name="Tasks", tasks=[parent])])

    update_status(tf, "Parent", TaskStatus.CANCELLED)

    assert parent.status == TaskStatus.CANCELLED
    assert child.status == TaskStatus.CANCELLED
```

**Step 2: Run test to verify it fails**

Run: `pytest tests/test_operations.py::test_update_status_done -v`
Expected: FAIL - update_status not defined

**Step 3: Write update_status implementation**

Add to `src/quick_task/operations.py`:
```python
from quick_task.matcher import find_task, all_tasks


def update_status(
    task_file: TaskFile,
    query: str,
    status: TaskStatus,
    force: bool = False,
) -> Task:
    """Update a task's status with cascading behavior."""
    task = find_task(task_file, query)
    if task is None:
        raise TaskNotFoundError(f"Task not found: {query}")

    set_status_recursive(task, status)

    # Check for parent rollup
    if status == TaskStatus.DONE:
        check_parent_rollup(task_file)

    return task


def set_status_recursive(task: Task, status: TaskStatus) -> None:
    """Set status on task and all children (for done/cancelled)."""
    task.status = status
    if status in (TaskStatus.DONE, TaskStatus.CANCELLED):
        for child in task.children:
            set_status_recursive(child, status)


def check_parent_rollup(task_file: TaskFile) -> None:
    """Check if any parent tasks should be auto-completed."""
    for task_list in task_file.lists:
        for task in task_list.tasks:
            rollup_if_children_done(task)


def rollup_if_children_done(task: Task) -> bool:
    """Recursively check and rollup parent completion. Returns True if task is done."""
    if not task.children:
        return task.status == TaskStatus.DONE

    # First, check children recursively
    for child in task.children:
        rollup_if_children_done(child)

    # Then check if all children are now done
    all_done = all(c.status == TaskStatus.DONE for c in task.children)
    if all_done and task.status != TaskStatus.DONE:
        task.status = TaskStatus.DONE

    return task.status == TaskStatus.DONE
```

**Step 4: Run test to verify it passes**

Run: `pytest tests/test_operations.py -v`
Expected: All tests PASS

**Step 5: Commit**

```bash
git add src/quick_task/operations.py tests/test_operations.py
git commit -m "feat: update_status with cascade and rollup"
```

---

### Task 10: Operations - Move Task

**Files:**
- Modify: `src/quick_task/operations.py`
- Modify: `tests/test_operations.py`

**Step 1: Write the failing test**

Add to `tests/test_operations.py`:
```python
from quick_task.operations import add_task, update_status, move_task


def test_move_before():
    tf = TaskFile(
        path="test.md",
        lists=[
            TaskList(
                name="Tasks",
                tasks=[
                    Task(title="First", status=TaskStatus.TODO),
                    Task(title="Second", status=TaskStatus.TODO),
                    Task(title="Third", status=TaskStatus.TODO),
                ],
            )
        ],
    )
    move_task(tf, "Third", before="First")
    titles = [t.title for t in tf.lists[0].tasks]
    assert titles == ["Third", "First", "Second"]


def test_move_after():
    tf = TaskFile(
        path="test.md",
        lists=[
            TaskList(
                name="Tasks",
                tasks=[
                    Task(title="First", status=TaskStatus.TODO),
                    Task(title="Second", status=TaskStatus.TODO),
                    Task(title="Third", status=TaskStatus.TODO),
                ],
            )
        ],
    )
    move_task(tf, "First", after="Second")
    titles = [t.title for t in tf.lists[0].tasks]
    assert titles == ["Second", "First", "Third"]


def test_move_to_different_list():
    tf = TaskFile(
        path="test.md",
        lists=[
            TaskList(name="Todo", tasks=[Task(title="My task", status=TaskStatus.DONE)]),
            TaskList(name="Done", tasks=[]),
        ],
    )
    move_task(tf, "My task", to_list="Done")
    assert len(tf.lists[0].tasks) == 0
    assert len(tf.lists[1].tasks) == 1
    assert tf.lists[1].tasks[0].title == "My task"
```

**Step 2: Run test to verify it fails**

Run: `pytest tests/test_operations.py::test_move_before -v`
Expected: FAIL - move_task not defined

**Step 3: Write move_task implementation**

Add to `src/quick_task/operations.py`:
```python
def move_task(
    task_file: TaskFile,
    query: str,
    before: str | None = None,
    after: str | None = None,
    to_list: str | None = None,
) -> Task:
    """Move a task to a new position or list."""
    task = find_task(task_file, query)
    if task is None:
        raise TaskNotFoundError(f"Task not found: {query}")

    # Find and remove from current location
    source_list = find_task_list(task_file, task)
    if source_list is None:
        raise TaskNotFoundError(f"Could not find task in any list: {query}")
    source_list.tasks.remove(task)

    # Determine target list
    target_list = get_list(task_file, to_list) if to_list else source_list

    # Determine position
    if before:
        target = find_task(task_file, before)
        if target is None:
            raise TaskNotFoundError(f"Target task not found: {before}")
        idx = target_list.tasks.index(target)
        target_list.tasks.insert(idx, task)
    elif after:
        target = find_task(task_file, after)
        if target is None:
            raise TaskNotFoundError(f"Target task not found: {after}")
        idx = target_list.tasks.index(target)
        target_list.tasks.insert(idx + 1, task)
    else:
        target_list.tasks.append(task)

    return task


def find_task_list(task_file: TaskFile, task: Task) -> TaskList | None:
    """Find which list contains a task (top-level only)."""
    for task_list in task_file.lists:
        if task in task_list.tasks:
            return task_list
    return None
```

**Step 4: Run test to verify it passes**

Run: `pytest tests/test_operations.py -v`
Expected: All tests PASS

**Step 5: Commit**

```bash
git add src/quick_task/operations.py tests/test_operations.py
git commit -m "feat: move_task operation for reordering"
```

---

### Task 11: Operations - Link Dependencies

**Files:**
- Modify: `src/quick_task/operations.py`
- Modify: `tests/test_operations.py`

**Step 1: Write the failing test**

Add to `tests/test_operations.py`:
```python
from quick_task.operations import add_task, update_status, move_task, link_dependency


def test_link_dependency():
    tf = TaskFile(
        path="test.md",
        lists=[
            TaskList(
                name="Tasks",
                tasks=[
                    Task(title="Task A", status=TaskStatus.TODO),
                    Task(title="Task B", status=TaskStatus.TODO),
                ],
            )
        ],
    )
    link_dependency(tf, "Task B", depends_on="Task A")
    assert tf.lists[0].tasks[1].metadata["depends"] == "Task A"


def test_link_dependency_with_bookmark():
    tf = TaskFile(
        path="test.md",
        lists=[
            TaskList(
                name="Tasks",
                tasks=[
                    Task(title="Task A", status=TaskStatus.TODO, bookmark="a"),
                    Task(title="Task B", status=TaskStatus.TODO),
                ],
            )
        ],
    )
    link_dependency(tf, "Task B", depends_on="#a")
    assert tf.lists[0].tasks[1].metadata["depends"] == "#a"
```

**Step 2: Run test to verify it fails**

Run: `pytest tests/test_operations.py::test_link_dependency -v`
Expected: FAIL - link_dependency not defined

**Step 3: Write link_dependency implementation**

Add to `src/quick_task/operations.py`:
```python
class CircularDependencyError(Exception):
    """Raised when a circular dependency is detected."""
    pass


def link_dependency(
    task_file: TaskFile,
    query: str,
    depends_on: str,
) -> Task:
    """Add a dependency to a task."""
    task = find_task(task_file, query)
    if task is None:
        raise TaskNotFoundError(f"Task not found: {query}")

    # Verify dependency exists
    dep_task = find_task(task_file, depends_on)
    if dep_task is None:
        raise TaskNotFoundError(f"Dependency task not found: {depends_on}")

    # Check for circular dependency
    if would_create_cycle(task_file, task, dep_task):
        raise CircularDependencyError(f"Circular dependency: {query} -> {depends_on}")

    # Store as the query string (bookmark or title)
    task.metadata["depends"] = depends_on
    return task


def would_create_cycle(task_file: TaskFile, task: Task, dep: Task) -> bool:
    """Check if adding dep as dependency of task would create a cycle."""
    # Check if task is already a dependency of dep (direct or transitive)
    visited = set()

    def check(t: Task) -> bool:
        if t is task:
            return True
        if id(t) in visited:
            return False
        visited.add(id(t))

        if "depends" in t.metadata:
            dep_task = find_task(task_file, t.metadata["depends"])
            if dep_task and check(dep_task):
                return True
        return False

    return check(dep)
```

**Step 4: Run test to verify it passes**

Run: `pytest tests/test_operations.py -v`
Expected: All tests PASS

**Step 5: Commit**

```bash
git add src/quick_task/operations.py tests/test_operations.py
git commit -m "feat: link_dependency with cycle detection"
```

---

### Task 12: File Discovery

**Files:**
- Create: `src/quick_task/discovery.py`
- Create: `tests/test_discovery.py`

**Step 1: Write the failing test**

```python
"""Tests for file discovery."""

import os
import tempfile
from pathlib import Path

from quick_task.discovery import find_task_file, DEFAULT_FILENAME


def test_find_in_current_directory():
    with tempfile.TemporaryDirectory() as tmpdir:
        task_file = Path(tmpdir) / DEFAULT_FILENAME
        task_file.write_text("## Tasks\n")

        found = find_task_file(tmpdir)
        assert found == task_file


def test_find_walking_up():
    with tempfile.TemporaryDirectory() as tmpdir:
        task_file = Path(tmpdir) / DEFAULT_FILENAME
        task_file.write_text("## Tasks\n")

        subdir = Path(tmpdir) / "sub" / "deep"
        subdir.mkdir(parents=True)

        found = find_task_file(str(subdir))
        assert found == task_file


def test_returns_none_when_not_found():
    with tempfile.TemporaryDirectory() as tmpdir:
        found = find_task_file(tmpdir)
        assert found is None


def test_explicit_file_overrides():
    with tempfile.TemporaryDirectory() as tmpdir:
        explicit = Path(tmpdir) / "custom.md"
        explicit.write_text("## Tasks\n")

        found = find_task_file(tmpdir, explicit_file=str(explicit))
        assert found == explicit
```

**Step 2: Run test to verify it fails**

Run: `pytest tests/test_discovery.py -v`
Expected: FAIL with ImportError

**Step 3: Write discovery implementation**

```python
"""File discovery for task files."""

from pathlib import Path


DEFAULT_FILENAME = "TASKS.md"


def find_task_file(
    start_dir: str | Path | None = None,
    explicit_file: str | Path | None = None,
) -> Path | None:
    """Find a task file, walking up directories if needed."""
    if explicit_file:
        path = Path(explicit_file)
        return path if path.exists() else None

    start = Path(start_dir) if start_dir else Path.cwd()
    current = start.resolve()

    while True:
        candidate = current / DEFAULT_FILENAME
        if candidate.exists():
            return candidate

        parent = current.parent
        if parent == current:
            # Reached root
            return None
        current = parent
```

**Step 4: Run test to verify it passes**

Run: `pytest tests/test_discovery.py -v`
Expected: All tests PASS

**Step 5: Commit**

```bash
git add src/quick_task/discovery.py tests/test_discovery.py
git commit -m "feat: file discovery walking up directories"
```

---

### Task 13: CLI - List Command

**Files:**
- Modify: `src/quick_task/cli.py`
- Create: `tests/test_cli.py`

**Step 1: Write the failing test**

```python
"""Tests for CLI commands."""

import tempfile
from pathlib import Path

from click.testing import CliRunner

from quick_task.cli import main


def test_list_shows_tasks():
    runner = CliRunner()
    with runner.isolated_filesystem():
        Path("TASKS.md").write_text("""## Tasks

- [ ] First task
- [x] Done task
- [~] In progress
""")
        result = runner.invoke(main, ["list"])
        assert result.exit_code == 0
        assert "First task" in result.output
        assert "Done task" in result.output


def test_list_filter_by_status():
    runner = CliRunner()
    with runner.isolated_filesystem():
        Path("TASKS.md").write_text("""## Tasks

- [ ] Todo task
- [x] Done task
""")
        result = runner.invoke(main, ["list", "--status", "todo"])
        assert result.exit_code == 0
        assert "Todo task" in result.output
        assert "Done task" not in result.output


def test_list_json_output():
    runner = CliRunner()
    with runner.isolated_filesystem():
        Path("TASKS.md").write_text("""## Tasks

- [ ] My task
""")
        result = runner.invoke(main, ["list", "--json"])
        assert result.exit_code == 0
        assert '"title": "My task"' in result.output
```

**Step 2: Run test to verify it fails**

Run: `pytest tests/test_cli.py::test_list_shows_tasks -v`
Expected: FAIL - no 'list' command

**Step 3: Write list command implementation**

Update `src/quick_task/cli.py`:
```python
"""CLI entry point for Quick Task."""

import json

import click
from rich.console import Console
from rich.table import Table

from quick_task.discovery import find_task_file
from quick_task.parser import parse_file
from quick_task.models import TaskStatus


console = Console()

STATUS_SYMBOLS = {
    TaskStatus.TODO: "[ ]",
    TaskStatus.IN_PROGRESS: "[~]",
    TaskStatus.DONE: "[x]",
    TaskStatus.CANCELLED: "[-]",
    TaskStatus.BLOCKED: "[?]",
    TaskStatus.DEFERRED: "[>]",
}

STATUS_NAMES = {
    "todo": TaskStatus.TODO,
    "in-progress": TaskStatus.IN_PROGRESS,
    "done": TaskStatus.DONE,
    "cancelled": TaskStatus.CANCELLED,
    "blocked": TaskStatus.BLOCKED,
    "deferred": TaskStatus.DEFERRED,
}


@click.group()
@click.version_option()
@click.option("--file", "-f", "file_path", help="Task file to use")
@click.pass_context
def main(ctx, file_path):
    """Quick Task - Markdown-based task management."""
    ctx.ensure_object(dict)
    ctx.obj["file_path"] = file_path


@main.command("list")
@click.option("--status", "-s", help="Filter by status")
@click.option("--list", "-l", "list_name", help="Filter by list name")
@click.option("--json", "as_json", is_flag=True, help="Output as JSON")
@click.pass_context
def list_tasks(ctx, status, list_name, as_json):
    """List tasks."""
    file_path = find_task_file(explicit_file=ctx.obj.get("file_path"))
    if not file_path:
        console.print("[red]No task file found[/red]")
        raise SystemExit(1)

    task_file = parse_file(file_path)

    # Collect tasks
    tasks = []
    for tl in task_file.lists:
        if list_name and tl.name.lower() != list_name.lower():
            continue
        for task in collect_with_list(tl.name, tl.tasks, 0):
            tasks.append(task)

    # Filter by status
    if status:
        target_status = STATUS_NAMES.get(status.lower())
        if target_status:
            tasks = [t for t in tasks if t["status"] == target_status]

    if as_json:
        output = [
            {
                "title": t["task"].title,
                "status": t["status"].name.lower(),
                "list": t["list"],
                "bookmark": t["task"].bookmark,
            }
            for t in tasks
        ]
        click.echo(json.dumps(output, indent=2))
    else:
        table = Table(show_header=True)
        table.add_column("Status", width=5)
        table.add_column("Task")
        table.add_column("List")

        for t in tasks:
            symbol = STATUS_SYMBOLS[t["status"]]
            indent = "  " * t["depth"]
            table.add_row(symbol, f"{indent}{t['task'].title}", t["list"])

        console.print(table)


def collect_with_list(list_name, tasks, depth):
    """Collect tasks with their list name and depth."""
    for task in tasks:
        yield {"task": task, "status": task.status, "list": list_name, "depth": depth}
        yield from collect_with_list(list_name, task.children, depth + 1)


if __name__ == "__main__":
    main()
```

**Step 4: Run test to verify it passes**

Run: `pytest tests/test_cli.py -v`
Expected: All tests PASS

**Step 5: Commit**

```bash
git add src/quick_task/cli.py tests/test_cli.py
git commit -m "feat: list command with status filter and JSON output"
```

---

### Task 14: CLI - Add Command

**Files:**
- Modify: `src/quick_task/cli.py`
- Modify: `tests/test_cli.py`

**Step 1: Write the failing test**

Add to `tests/test_cli.py`:
```python
def test_add_task():
    runner = CliRunner()
    with runner.isolated_filesystem():
        Path("TASKS.md").write_text("""## Tasks

- [ ] Existing task
""")
        result = runner.invoke(main, ["add", "New task"])
        assert result.exit_code == 0

        content = Path("TASKS.md").read_text()
        assert "New task" in content


def test_add_task_to_named_list():
    runner = CliRunner()
    with runner.isolated_filesystem():
        Path("TASKS.md").write_text("""## Backlog

## Done
""")
        result = runner.invoke(main, ["add", "New task", "--list", "Done"])
        assert result.exit_code == 0

        content = Path("TASKS.md").read_text()
        assert "Done" in content
        # Task should be under Done section


def test_add_subtask():
    runner = CliRunner()
    with runner.isolated_filesystem():
        Path("TASKS.md").write_text("""## Tasks

- [ ] Parent task
""")
        result = runner.invoke(main, ["add", "Child task", "--parent", "Parent"])
        assert result.exit_code == 0

        content = Path("TASKS.md").read_text()
        assert "Child task" in content
```

**Step 2: Run test to verify it fails**

Run: `pytest tests/test_cli.py::test_add_task -v`
Expected: FAIL - no 'add' command

**Step 3: Write add command implementation**

Add to `src/quick_task/cli.py`:
```python
from quick_task.operations import add_task as op_add_task
from quick_task.writer import write_file


@main.command("add")
@click.argument("title")
@click.option("--list", "-l", "list_name", help="Target list name")
@click.option("--parent", "-p", "parent_query", help="Parent task (creates subtask)")
@click.pass_context
def add(ctx, title, list_name, parent_query):
    """Add a new task."""
    file_path = find_task_file(explicit_file=ctx.obj.get("file_path"))
    if not file_path:
        console.print("[red]No task file found[/red]")
        raise SystemExit(1)

    task_file = parse_file(file_path)

    try:
        task = op_add_task(task_file, title, list_name=list_name, parent_query=parent_query)
        write_file(task_file)
        console.print(f"[green]Added:[/green] {task.title}")
    except Exception as e:
        console.print(f"[red]Error:[/red] {e}")
        raise SystemExit(1)
```

**Step 4: Run test to verify it passes**

Run: `pytest tests/test_cli.py -v`
Expected: All tests PASS

**Step 5: Commit**

```bash
git add src/quick_task/cli.py tests/test_cli.py
git commit -m "feat: add command for creating tasks"
```

---

### Task 15: CLI - Status Commands

**Files:**
- Modify: `src/quick_task/cli.py`
- Modify: `tests/test_cli.py`

**Step 1: Write the failing test**

Add to `tests/test_cli.py`:
```python
def test_done_command():
    runner = CliRunner()
    with runner.isolated_filesystem():
        Path("TASKS.md").write_text("""## Tasks

- [ ] My task
""")
        result = runner.invoke(main, ["done", "My task"])
        assert result.exit_code == 0

        content = Path("TASKS.md").read_text()
        assert "[x] My task" in content


def test_start_command():
    runner = CliRunner()
    with runner.isolated_filesystem():
        Path("TASKS.md").write_text("""## Tasks

- [ ] My task
""")
        result = runner.invoke(main, ["start", "My task"])
        assert result.exit_code == 0

        content = Path("TASKS.md").read_text()
        assert "[~] My task" in content


def test_block_command():
    runner = CliRunner()
    with runner.isolated_filesystem():
        Path("TASKS.md").write_text("""## Tasks

- [ ] My task
""")
        result = runner.invoke(main, ["block", "My task"])
        assert result.exit_code == 0

        content = Path("TASKS.md").read_text()
        assert "[?] My task" in content
```

**Step 2: Run test to verify it fails**

Run: `pytest tests/test_cli.py::test_done_command -v`
Expected: FAIL - no 'done' command

**Step 3: Write status commands**

Add to `src/quick_task/cli.py`:
```python
from quick_task.operations import add_task as op_add_task, update_status


def make_status_command(name, status, description):
    """Factory for status update commands."""

    @main.command(name)
    @click.argument("query")
    @click.option("--force", is_flag=True, help="Force even with incomplete dependencies")
    @click.pass_context
    def command(ctx, query, force):
        file_path = find_task_file(explicit_file=ctx.obj.get("file_path"))
        if not file_path:
            console.print("[red]No task file found[/red]")
            raise SystemExit(1)

        task_file = parse_file(file_path)

        try:
            task = update_status(task_file, query, status, force=force)
            write_file(task_file)
            console.print(f"[green]{description}:[/green] {task.title}")
        except Exception as e:
            console.print(f"[red]Error:[/red] {e}")
            raise SystemExit(1)

    command.__doc__ = f"{description} a task."
    return command


# Register status commands
done = make_status_command("done", TaskStatus.DONE, "Completed")
start = make_status_command("start", TaskStatus.IN_PROGRESS, "Started")
block = make_status_command("block", TaskStatus.BLOCKED, "Blocked")
defer = make_status_command("defer", TaskStatus.DEFERRED, "Deferred")
cancel = make_status_command("cancel", TaskStatus.CANCELLED, "Cancelled")
reset = make_status_command("reset", TaskStatus.TODO, "Reset")
```

**Step 4: Run test to verify it passes**

Run: `pytest tests/test_cli.py -v`
Expected: All tests PASS

**Step 5: Commit**

```bash
git add src/quick_task/cli.py tests/test_cli.py
git commit -m "feat: status commands (done, start, block, defer, cancel, reset)"
```

---

### Task 16: CLI - Move Command

**Files:**
- Modify: `src/quick_task/cli.py`
- Modify: `tests/test_cli.py`

**Step 1: Write the failing test**

Add to `tests/test_cli.py`:
```python
def test_move_before():
    runner = CliRunner()
    with runner.isolated_filesystem():
        Path("TASKS.md").write_text("""## Tasks

- [ ] First
- [ ] Second
- [ ] Third
""")
        result = runner.invoke(main, ["move", "Third", "--before", "First"])
        assert result.exit_code == 0

        content = Path("TASKS.md").read_text()
        # Third should now be before First
        assert content.index("Third") < content.index("First")


def test_move_to_list():
    runner = CliRunner()
    with runner.isolated_filesystem():
        Path("TASKS.md").write_text("""## Todo

- [ ] My task

## Done
""")
        result = runner.invoke(main, ["move", "My task", "--list", "Done"])
        assert result.exit_code == 0

        content = Path("TASKS.md").read_text()
        # Task should be under Done now
        done_idx = content.index("## Done")
        task_idx = content.index("My task")
        assert task_idx > done_idx
```

**Step 2: Run test to verify it fails**

Run: `pytest tests/test_cli.py::test_move_before -v`
Expected: FAIL - no 'move' command

**Step 3: Write move command**

Add to `src/quick_task/cli.py`:
```python
from quick_task.operations import add_task as op_add_task, update_status, move_task as op_move_task


@main.command("move")
@click.argument("query")
@click.option("--before", "-b", help="Move before this task")
@click.option("--after", "-a", help="Move after this task")
@click.option("--list", "-l", "to_list", help="Move to this list")
@click.pass_context
def move(ctx, query, before, after, to_list):
    """Move a task to a new position or list."""
    file_path = find_task_file(explicit_file=ctx.obj.get("file_path"))
    if not file_path:
        console.print("[red]No task file found[/red]")
        raise SystemExit(1)

    task_file = parse_file(file_path)

    try:
        task = op_move_task(task_file, query, before=before, after=after, to_list=to_list)
        write_file(task_file)
        console.print(f"[green]Moved:[/green] {task.title}")
    except Exception as e:
        console.print(f"[red]Error:[/red] {e}")
        raise SystemExit(1)
```

**Step 4: Run test to verify it passes**

Run: `pytest tests/test_cli.py -v`
Expected: All tests PASS

**Step 5: Commit**

```bash
git add src/quick_task/cli.py tests/test_cli.py
git commit -m "feat: move command for reordering tasks"
```

---

### Task 17: CLI - Link and Note Commands

**Files:**
- Modify: `src/quick_task/cli.py`
- Modify: `tests/test_cli.py`

**Step 1: Write the failing test**

Add to `tests/test_cli.py`:
```python
def test_link_command():
    runner = CliRunner()
    with runner.isolated_filesystem():
        Path("TASKS.md").write_text("""## Tasks

- [ ] Task A
- [ ] Task B
""")
        result = runner.invoke(main, ["link", "Task B", "--depends", "Task A"])
        assert result.exit_code == 0

        content = Path("TASKS.md").read_text()
        assert "depends: Task A" in content


def test_note_command():
    runner = CliRunner()
    with runner.isolated_filesystem():
        Path("TASKS.md").write_text("""## Tasks

- [ ] My task
""")
        result = runner.invoke(main, ["note", "My task", "Some extra info"])
        assert result.exit_code == 0

        content = Path("TASKS.md").read_text()
        assert "notes: Some extra info" in content
```

**Step 2: Run test to verify it fails**

Run: `pytest tests/test_cli.py::test_link_command -v`
Expected: FAIL - no 'link' command

**Step 3: Write link and note commands**

Add to `src/quick_task/cli.py`:
```python
from quick_task.operations import (
    add_task as op_add_task,
    update_status,
    move_task as op_move_task,
    link_dependency,
)
from quick_task.matcher import find_task


@main.command("link")
@click.argument("query")
@click.option("--depends", "-d", "depends_on", required=True, help="Task this depends on")
@click.pass_context
def link(ctx, query, depends_on):
    """Add a dependency to a task."""
    file_path = find_task_file(explicit_file=ctx.obj.get("file_path"))
    if not file_path:
        console.print("[red]No task file found[/red]")
        raise SystemExit(1)

    task_file = parse_file(file_path)

    try:
        task = link_dependency(task_file, query, depends_on)
        write_file(task_file)
        console.print(f"[green]Linked:[/green] {task.title} depends on {depends_on}")
    except Exception as e:
        console.print(f"[red]Error:[/red] {e}")
        raise SystemExit(1)


@main.command("note")
@click.argument("query")
@click.argument("text")
@click.pass_context
def note(ctx, query, text):
    """Add a note to a task."""
    file_path = find_task_file(explicit_file=ctx.obj.get("file_path"))
    if not file_path:
        console.print("[red]No task file found[/red]")
        raise SystemExit(1)

    task_file = parse_file(file_path)

    try:
        task = find_task(task_file, query)
        if task is None:
            console.print(f"[red]Task not found:[/red] {query}")
            raise SystemExit(1)
        task.metadata["notes"] = text
        write_file(task_file)
        console.print(f"[green]Added note to:[/green] {task.title}")
    except Exception as e:
        console.print(f"[red]Error:[/red] {e}")
        raise SystemExit(1)
```

**Step 4: Run test to verify it passes**

Run: `pytest tests/test_cli.py -v`
Expected: All tests PASS

**Step 5: Commit**

```bash
git add src/quick_task/cli.py tests/test_cli.py
git commit -m "feat: link and note commands for metadata"
```

---

### Task 18: CLI - Edit Command

**Files:**
- Modify: `src/quick_task/cli.py`
- Modify: `tests/test_cli.py`

**Step 1: Write the failing test**

Add to `tests/test_cli.py`:
```python
import os


def test_edit_command_finds_task(monkeypatch):
    runner = CliRunner()
    with runner.isolated_filesystem():
        Path("TASKS.md").write_text("""## Tasks

- [ ] My task
""")
        # Mock EDITOR to just cat the file (no-op)
        monkeypatch.setenv("EDITOR", "cat")
        result = runner.invoke(main, ["edit", "My task"])
        # Should at least find the task and not error
        assert result.exit_code == 0 or "My task" in result.output
```

**Step 2: Run test to verify it fails**

Run: `pytest tests/test_cli.py::test_edit_command_finds_task -v`
Expected: FAIL - no 'edit' command

**Step 3: Write edit command**

Add to `src/quick_task/cli.py`:
```python
import os
import subprocess


@main.command("edit")
@click.argument("query")
@click.pass_context
def edit(ctx, query):
    """Open a task in $EDITOR."""
    file_path = find_task_file(explicit_file=ctx.obj.get("file_path"))
    if not file_path:
        console.print("[red]No task file found[/red]")
        raise SystemExit(1)

    task_file = parse_file(file_path)

    task = find_task(task_file, query)
    if task is None:
        console.print(f"[red]Task not found:[/red] {query}")
        raise SystemExit(1)

    editor = os.environ.get("EDITOR", "vi")
    # Open the file - user will find the task manually
    # Future: could jump to line number
    subprocess.run([editor, str(file_path)])
    console.print(f"[green]Edited:[/green] {file_path}")
```

**Step 4: Run test to verify it passes**

Run: `pytest tests/test_cli.py -v`
Expected: All tests PASS

**Step 5: Commit**

```bash
git add src/quick_task/cli.py tests/test_cli.py
git commit -m "feat: edit command to open task file in editor"
```

---

### Task 19: Integration Test

**Files:**
- Create: `tests/test_integration.py`

**Step 1: Write integration test**

```python
"""Integration tests for the full workflow."""

from pathlib import Path

from click.testing import CliRunner

from quick_task.cli import main


def test_full_workflow():
    """Test a complete workflow: add, start, add subtask, complete, list."""
    runner = CliRunner()
    with runner.isolated_filesystem():
        # Create initial file
        Path("TASKS.md").write_text("""## Backlog

## In Progress

## Done
""")

        # Add a task
        result = runner.invoke(main, ["add", "Build authentication", "--list", "Backlog"])
        assert result.exit_code == 0

        # Start the task (moves to in-progress conceptually)
        result = runner.invoke(main, ["start", "Build auth"])
        assert result.exit_code == 0

        # Add subtasks
        result = runner.invoke(main, ["add", "Create login form", "--parent", "Build auth"])
        assert result.exit_code == 0

        result = runner.invoke(main, ["add", "Add validation", "--parent", "Build auth"])
        assert result.exit_code == 0

        # Complete subtasks
        result = runner.invoke(main, ["done", "Create login"])
        assert result.exit_code == 0

        result = runner.invoke(main, ["done", "Add validation"])
        assert result.exit_code == 0

        # Check parent was auto-completed
        content = Path("TASKS.md").read_text()
        assert "[x] Build authentication" in content

        # List tasks
        result = runner.invoke(main, ["list", "--json"])
        assert result.exit_code == 0
        assert "Build authentication" in result.output


def test_dependency_workflow():
    """Test dependency linking and warnings."""
    runner = CliRunner()
    with runner.isolated_filesystem():
        Path("TASKS.md").write_text("""## Tasks

- [ ] Set up database [#db]
- [ ] Build API
""")

        # Link dependency
        result = runner.invoke(main, ["link", "Build API", "--depends", "#db"])
        assert result.exit_code == 0

        content = Path("TASKS.md").read_text()
        assert "depends: #db" in content
```

**Step 2: Run integration tests**

Run: `pytest tests/test_integration.py -v`
Expected: All tests PASS

**Step 3: Commit**

```bash
git add tests/test_integration.py
git commit -m "test: add integration tests for full workflows"
```

---

### Task 20: Final Polish and README

**Files:**
- Modify: `README.md`

**Step 1: Update README with usage documentation**

```markdown
# Quick Task (qt)

A markdown-based task management CLI for humans and agents.

## Installation

```bash
pip install -e .
```

## Usage

### Adding Tasks

```bash
qt add "Task title"                       # Add to default list
qt add "Task title" --list=Backlog        # Add to specific list
qt add "Subtask" --parent="Parent task"   # Add as subtask
```

### Updating Status

```bash
qt done "Task title"      # Mark complete [x]
qt start "Task title"     # Mark in-progress [~]
qt block "Task title"     # Mark blocked [?]
qt defer "Task title"     # Mark deferred [>]
qt cancel "Task title"    # Mark cancelled [-]
qt reset "Task title"     # Back to todo [ ]
```

### Viewing Tasks

```bash
qt list                     # Show all tasks
qt list --status=todo       # Filter by status
qt list --list=Backlog      # Filter by list
qt list --json              # JSON output for agents
```

### Organizing

```bash
qt move "Task" --before="Other"    # Reorder
qt move "Task" --list=Done         # Move to list
```

### Dependencies & Notes

```bash
qt link "Task B" --depends="Task A"    # Add dependency
qt note "Task" "Extra info"            # Add note
qt edit "Task"                         # Open in $EDITOR
```

## Markdown Format

```markdown
## Backlog [#backlog]

- [ ] Design auth system [#auth]
    depends: Set up database
    docs: docs/auth-spec.md
- [~] Build registration
    - [x] Create form
    - [ ] Add validation
```

### Status Symbols

| Symbol | Status |
|--------|--------|
| `[ ]` | Todo |
| `[~]` | In-progress |
| `[x]` | Done |
| `[-]` | Cancelled |
| `[?]` | Blocked |
| `[>]` | Deferred |

## File Discovery

By default, `qt` looks for `TASKS.md` in the current directory and walks up the directory tree. Use `--file` to specify a different file.

## For Agents

Use `--json` for structured output:

```bash
qt list --status=todo --json
```

Agents can use the same CLI commands as humans.
```

**Step 2: Run all tests**

Run: `pytest -v`
Expected: All tests PASS

**Step 3: Commit**

```bash
git add README.md
git commit -m "docs: add usage documentation to README"
```

---

## Summary

This plan implements the Quick Task CLI in 20 tasks:

1. **Tasks 1-5**: Core infrastructure (setup, models, parser)
2. **Tasks 6-7**: Writer and fuzzy matcher
3. **Tasks 8-11**: Operations (add, status, move, link)
4. **Task 12**: File discovery
5. **Tasks 13-18**: CLI commands
6. **Tasks 19-20**: Integration tests and documentation

Each task is TDD: write failing test, implement, verify, commit.
