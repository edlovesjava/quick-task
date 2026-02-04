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
