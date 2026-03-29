"""Tests for task operations."""

from quick_task.models import Task, TaskList, TaskFile, TaskStatus
from quick_task.operations import add_task, update_status, move_task, link_dependency


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


def test_link_doc():
    from quick_task.operations import link_doc

    tf = TaskFile(
        path="test.md",
        lists=[
            TaskList(
                name="Tasks",
                tasks=[Task(title="Auth system", status=TaskStatus.TODO)],
            )
        ],
    )
    link_doc(tf, "Auth system", "docs/auth-spec.md")
    assert tf.lists[0].tasks[0].metadata["docs"] == "docs/auth-spec.md"


def test_link_doc_appends():
    from quick_task.operations import link_doc

    task = Task(
        title="Auth system",
        status=TaskStatus.TODO,
        metadata={"docs": "docs/design.md"},
    )
    tf = TaskFile(
        path="test.md",
        lists=[TaskList(name="Tasks", tasks=[task])],
    )
    link_doc(tf, "Auth system", "docs/auth-spec.md")
    assert "docs/design.md" in tf.lists[0].tasks[0].metadata["docs"]
    assert "docs/auth-spec.md" in tf.lists[0].tasks[0].metadata["docs"]


def test_link_doc_with_section():
    from quick_task.operations import link_doc

    tf = TaskFile(
        path="test.md",
        lists=[
            TaskList(
                name="Tasks",
                tasks=[Task(title="Auth system", status=TaskStatus.TODO)],
            )
        ],
    )
    link_doc(tf, "Auth system", "docs/plan.md#cli-commands")
    assert tf.lists[0].tasks[0].metadata["docs"] == "docs/plan.md#cli-commands"


def test_link_doc_no_duplicates():
    from quick_task.operations import link_doc

    task = Task(
        title="Auth system",
        status=TaskStatus.TODO,
        metadata={"docs": "docs/design.md"},
    )
    tf = TaskFile(
        path="test.md",
        lists=[TaskList(name="Tasks", tasks=[task])],
    )
    link_doc(tf, "Auth system", "docs/design.md")
    # Should not duplicate
    assert tf.lists[0].tasks[0].metadata["docs"] == "docs/design.md"


def test_remove_top_level_task():
    from quick_task.operations import remove_task

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
    remove_task(tf, "Task A")
    assert len(tf.lists[0].tasks) == 1
    assert tf.lists[0].tasks[0].title == "Task B"


def test_remove_subtask():
    from quick_task.operations import remove_task

    child = Task(title="Child", status=TaskStatus.TODO)
    parent = Task(title="Parent", status=TaskStatus.TODO, children=[child])
    tf = TaskFile(path="test.md", lists=[TaskList(name="Tasks", tasks=[parent])])

    remove_task(tf, "Child")
    assert len(tf.lists[0].tasks) == 1
    assert len(tf.lists[0].tasks[0].children) == 0


def test_remove_task_not_found():
    import pytest
    from quick_task.operations import remove_task, TaskNotFoundError

    tf = TaskFile(
        path="test.md",
        lists=[TaskList(name="Tasks", tasks=[])],
    )
    with pytest.raises(TaskNotFoundError):
        remove_task(tf, "nonexistent")


def test_rename_task():
    from quick_task.operations import rename_task

    child = Task(title="Child", status=TaskStatus.TODO)
    task = Task(title="Old name", status=TaskStatus.IN_PROGRESS, bookmark="t", children=[child])
    tf = TaskFile(path="test.md", lists=[TaskList(name="Tasks", tasks=[task])])

    rename_task(tf, "Old name", "New name")
    assert tf.lists[0].tasks[0].title == "New name"
    assert tf.lists[0].tasks[0].status == TaskStatus.IN_PROGRESS
    assert tf.lists[0].tasks[0].bookmark == "t"
    assert len(tf.lists[0].tasks[0].children) == 1


def test_link_dependency_circular_detection():
    import pytest
    from quick_task.operations import CircularDependencyError

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
    # A depends on B
    link_dependency(tf, "Task A", depends_on="Task B")
    # B depends on A would create a cycle
    with pytest.raises(CircularDependencyError):
        link_dependency(tf, "Task B", depends_on="Task A")


# ---------------------------------------------------------------------------
# Metadata: add_task with assignee / priority
# ---------------------------------------------------------------------------

def test_add_task_with_assignee():
    tf = make_empty_task_file()
    task = add_task(tf, "My task", assignee="@builder")
    assert task.metadata.get("assignee") == "@builder"


def test_add_task_with_priority():
    tf = make_empty_task_file()
    task = add_task(tf, "My task", priority="high")
    assert task.metadata.get("priority") == "high"


def test_add_task_priority_is_lowercased():
    tf = make_empty_task_file()
    task = add_task(tf, "My task", priority="HIGH")
    assert task.metadata.get("priority") == "high"


def test_add_task_invalid_priority_raises():
    import pytest
    tf = make_empty_task_file()
    with pytest.raises(ValueError, match="Invalid priority"):
        add_task(tf, "My task", priority="urgent")


def test_add_task_with_stamp_created():
    tf = make_empty_task_file()
    task = add_task(tf, "My task", stamp_created=True)
    assert "created" in task.metadata
    # Basic ISO format check
    import re
    assert re.match(r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z$", task.metadata["created"])


def test_add_task_without_stamp_created():
    tf = make_empty_task_file()
    task = add_task(tf, "My task", stamp_created=False)
    assert "created" not in task.metadata


# ---------------------------------------------------------------------------
# Metadata: set_task_metadata
# ---------------------------------------------------------------------------

def test_set_task_metadata_assignee():
    from quick_task.operations import set_task_metadata

    task = Task(title="My task", status=TaskStatus.TODO)
    tf = TaskFile(path="test.md", lists=[TaskList(name="Tasks", tasks=[task])])

    set_task_metadata(tf, "My task", assignee="@planner")
    assert task.metadata.get("assignee") == "@planner"


def test_set_task_metadata_priority():
    from quick_task.operations import set_task_metadata

    task = Task(title="My task", status=TaskStatus.TODO)
    tf = TaskFile(path="test.md", lists=[TaskList(name="Tasks", tasks=[task])])

    set_task_metadata(tf, "My task", priority="critical")
    assert task.metadata.get("priority") == "critical"


def test_set_task_metadata_stamps_updated():
    from quick_task.operations import set_task_metadata
    import re

    task = Task(title="My task", status=TaskStatus.TODO)
    tf = TaskFile(path="test.md", lists=[TaskList(name="Tasks", tasks=[task])])

    set_task_metadata(tf, "My task", assignee="@builder")
    assert "updated" in task.metadata
    assert re.match(r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z$", task.metadata["updated"])


def test_set_task_metadata_no_stamp_updated():
    from quick_task.operations import set_task_metadata

    task = Task(title="My task", status=TaskStatus.TODO)
    tf = TaskFile(path="test.md", lists=[TaskList(name="Tasks", tasks=[task])])

    set_task_metadata(tf, "My task", assignee="@builder", stamp_updated=False)
    assert "updated" not in task.metadata


def test_set_task_metadata_clears_assignee():
    from quick_task.operations import set_task_metadata

    task = Task(title="My task", status=TaskStatus.TODO, metadata={"assignee": "@builder"})
    tf = TaskFile(path="test.md", lists=[TaskList(name="Tasks", tasks=[task])])

    set_task_metadata(tf, "My task", assignee="", stamp_updated=False)
    assert "assignee" not in task.metadata
