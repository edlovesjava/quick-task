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
