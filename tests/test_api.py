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


# ---------------------------------------------------------------------------
# Metadata API: list_tasks with assignee / priority filters
# ---------------------------------------------------------------------------

METADATA_MD = """\
## Tasks

- [ ] Alpha task [#alpha]
    assignee: @builder
    priority: high
- [ ] Beta task [#beta]
    assignee: @planner
    priority: low
- [ ] Gamma task [#gamma]
    assignee: @builder
    priority: critical
- [ ] Unassigned task [#unassigned]
"""


def make_metadata_task_file():
    return parse_content(METADATA_MD, "test.md")


def test_list_tasks_filter_by_assignee():
    tf = make_metadata_task_file()
    tasks = list_tasks(tf, assignee="@builder")
    titles = [t.title for t in tasks]
    assert "Alpha task" in titles
    assert "Gamma task" in titles
    assert "Beta task" not in titles
    assert "Unassigned task" not in titles


def test_list_tasks_filter_by_priority():
    tf = make_metadata_task_file()
    tasks = list_tasks(tf, priority="high")
    titles = [t.title for t in tasks]
    assert "Alpha task" in titles
    assert "Beta task" not in titles
    assert "Gamma task" not in titles


def test_list_tasks_filter_assignee_case_insensitive():
    tf = parse_content("""\
## Tasks

- [ ] My task
    assignee: @Builder
""", "test.md")
    tasks = list_tasks(tf, assignee="@builder")
    assert len(tasks) == 1
    assert tasks[0].title == "My task"


def test_list_tasks_filter_priority_case_insensitive():
    tf = parse_content("""\
## Tasks

- [ ] My task
    priority: HIGH
""", "test.md")
    tasks = list_tasks(tf, priority="high")
    assert len(tasks) == 1


def test_list_tasks_filter_assignee_and_priority():
    tf = make_metadata_task_file()
    tasks = list_tasks(tf, assignee="@builder", priority="high")
    assert len(tasks) == 1
    assert tasks[0].title == "Alpha task"


def test_list_tasks_filter_assignee_no_match():
    tf = make_metadata_task_file()
    tasks = list_tasks(tf, assignee="@nobody")
    assert tasks == []


def test_list_tasks_filter_priority_no_match():
    tf = make_metadata_task_file()
    tasks = list_tasks(tf, priority="medium")
    assert tasks == []


# ---------------------------------------------------------------------------
# Metadata API: set_task_metadata exposed in __all__
# ---------------------------------------------------------------------------

def test_set_task_metadata_in_api():
    """set_task_metadata is importable from quick_task.api."""
    from quick_task.api import set_task_metadata
    assert callable(set_task_metadata)


def test_set_task_metadata_via_api():
    from quick_task.api import set_task_metadata

    tf = make_metadata_task_file()
    task = get_task(tf, "#unassigned")
    set_task_metadata(tf, "#unassigned", assignee="@runner", stamp_updated=False)
    assert task.metadata.get("assignee") == "@runner"


# ---------------------------------------------------------------------------
# Metadata API: metadata.py symbols exported from api.__all__
# ---------------------------------------------------------------------------

def test_metadata_constants_in_api_all():
    import quick_task.api as api_module
    for name in ("FIELD_ASSIGNEE", "FIELD_PRIORITY", "FIELD_CREATED", "FIELD_UPDATED",
                 "VALID_PRIORITIES", "validate_priority", "now_iso"):
        assert name in api_module.__all__, f"{name} not in api.__all__"


def test_metadata_constants_importable_from_api():
    from quick_task.api import (
        FIELD_ASSIGNEE, FIELD_PRIORITY, FIELD_CREATED, FIELD_UPDATED,
        VALID_PRIORITIES, validate_priority, now_iso,
    )
    assert FIELD_ASSIGNEE == "assignee"
    assert FIELD_PRIORITY == "priority"
    assert FIELD_CREATED == "created"
    assert FIELD_UPDATED == "updated"
    assert "high" in VALID_PRIORITIES
    assert callable(validate_priority)
    assert callable(now_iso)
