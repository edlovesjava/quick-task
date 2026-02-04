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
