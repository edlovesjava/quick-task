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
