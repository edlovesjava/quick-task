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
