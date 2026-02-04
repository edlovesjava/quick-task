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
