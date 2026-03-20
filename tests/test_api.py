"""Tests for the programmatic API module."""

import pytest
from pathlib import Path

from quick_task.api import (
    load_file,
    save,
    get_task,
    list_tasks,
    add_task,
    update_status,
    find_tasks,
    all_tasks,
    Task,
    TaskList,
    TaskFile,
    TaskStatus,
    TaskNotFoundError,
    AmbiguousMatchError,
    parse_content,
    write_content,
    check_content,
)


SAMPLE_MD = """\
## Backlog [#backlog]

- [ ] Build API [#build-api]
    depends: #design
- [ ] Write tests [#write-tests]
    depends: #build-api
- [x] Design system [#design]

## Done [#done]

- [x] Setup project [#setup]
"""


def make_task_file():
    return parse_content(SAMPLE_MD, "test.md")


# --- load_file ---

def test_load_file_with_path(tmp_path):
    p = tmp_path / "TASKS.md"
    p.write_text(SAMPLE_MD)
    tf = load_file(p)
    assert len(tf.lists) == 2
    assert tf.lists[0].name == "Backlog"


def test_load_file_missing_path():
    with pytest.raises(FileNotFoundError):
        load_file("/nonexistent/TASKS.md")


def test_load_file_auto_discover(tmp_path, monkeypatch):
    p = tmp_path / "TASKS.md"
    p.write_text(SAMPLE_MD)
    monkeypatch.chdir(tmp_path)
    tf = load_file()
    assert len(tf.lists) == 2


def test_load_file_auto_discover_not_found(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    with pytest.raises(FileNotFoundError):
        load_file()


# --- get_task ---

def test_get_task_by_bookmark():
    tf = make_task_file()
    task = get_task(tf, "#build-api")
    assert task.title == "Build API"


def test_get_task_by_title():
    tf = make_task_file()
    task = get_task(tf, "Write tests")
    assert task.bookmark == "write-tests"


def test_get_task_not_found():
    tf = make_task_file()
    with pytest.raises(TaskNotFoundError):
        get_task(tf, "nonexistent task")


def test_get_task_ambiguous():
    tf = TaskFile(
        path="test.md",
        lists=[
            TaskList(
                name="Tasks",
                tasks=[
                    Task(title="Build frontend", status=TaskStatus.TODO),
                    Task(title="Build backend", status=TaskStatus.TODO),
                ],
            )
        ],
    )
    with pytest.raises(AmbiguousMatchError):
        get_task(tf, "Build")


# --- list_tasks ---

def test_list_tasks_all():
    tf = make_task_file()
    tasks = list_tasks(tf)
    assert len(tasks) == 4  # 3 in Backlog + 1 in Done (top-level only)


def test_list_tasks_filter_by_list():
    tf = make_task_file()
    tasks = list_tasks(tf, list_name="Backlog")
    assert len(tasks) == 3


def test_list_tasks_filter_by_status():
    tf = make_task_file()
    tasks = list_tasks(tf, status=TaskStatus.DONE)
    assert len(tasks) == 2  # Design system + Setup project


def test_list_tasks_filter_both():
    tf = make_task_file()
    tasks = list_tasks(tf, list_name="Done", status=TaskStatus.DONE)
    assert len(tasks) == 1
    assert tasks[0].title == "Setup project"


def test_list_tasks_flat_includes_children():
    parent = Task(
        title="Parent",
        status=TaskStatus.TODO,
        children=[Task(title="Child", status=TaskStatus.TODO)],
    )
    tf = TaskFile(path="test.md", lists=[TaskList(name="Tasks", tasks=[parent])])
    flat = list_tasks(tf, flat=True)
    assert len(flat) == 2
    top = list_tasks(tf, flat=False)
    assert len(top) == 1


# --- add_task via API ---

def test_add_task_via_api():
    tf = make_task_file()
    task = add_task(tf, "New task", list_name="Done")
    assert task.title == "New task"
    assert len(tf.lists[1].tasks) == 2


# --- update_status via API ---

def test_update_status_via_api():
    tf = make_task_file()
    task = update_status(tf, "#build-api", TaskStatus.IN_PROGRESS)
    assert task.status == TaskStatus.IN_PROGRESS


# --- save round-trip ---

def test_save_round_trip(tmp_path):
    p = tmp_path / "TASKS.md"
    p.write_text(SAMPLE_MD)
    tf = load_file(p)
    add_task(tf, "Round-trip task")
    save(tf)
    tf2 = load_file(p)
    titles = [t.title for t in all_tasks(tf2)]
    assert "Round-trip task" in titles


# --- write_content / check_content ---

def test_write_content_produces_valid_markdown():
    tf = make_task_file()
    content = write_content(tf)
    issues = check_content(content)
    assert len(issues) == 0


# --- find_tasks ---

def test_find_tasks_multiple():
    tf = make_task_file()
    results = find_tasks(tf, "#build-api")
    assert len(results) == 1


# --- all_tasks ---

def test_all_tasks_count():
    tf = make_task_file()
    assert len(all_tasks(tf)) == 4
