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


def test_parse_metadata_and_bookmarks():
    task_file = parse_file(FIXTURES / "metadata.md")

    assert task_file.lists[0].name == "Backlog"
    assert task_file.lists[0].bookmark == "backlog"

    tasks = task_file.lists[0].tasks
    assert tasks[0].title == "Complex task"
    assert tasks[0].bookmark == "complex"
    assert tasks[0].metadata["depends"] == "Other task"
    assert tasks[0].metadata["docs"] == "docs/spec.md"
