"""Task operations - add, update, move, etc."""

from quick_task.models import Task, TaskList, TaskFile, TaskStatus
from quick_task.matcher import find_task


class TaskNotFoundError(Exception):
    """Raised when a task cannot be found."""
    pass


class ListNotFoundError(Exception):
    """Raised when a task list cannot be found."""
    pass


class CircularDependencyError(Exception):
    """Raised when a circular dependency is detected."""
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


def move_task(
    task_file: TaskFile,
    query: str,
    before: str | None = None,
    after: str | None = None,
    to_list: str | None = None,
) -> Task:
    """Move a task to a new position or list."""
    task = find_task(task_file, query)
    if task is None:
        raise TaskNotFoundError(f"Task not found: {query}")

    # Find and remove from current location
    source_list = find_task_list(task_file, task)
    if source_list is None:
        raise TaskNotFoundError(f"Could not find task in any list: {query}")
    source_list.tasks.remove(task)

    # Determine target list
    target_list = get_list(task_file, to_list) if to_list else source_list

    # Determine position
    if before:
        target = find_task(task_file, before)
        if target is None:
            raise TaskNotFoundError(f"Target task not found: {before}")
        try:
            idx = target_list.tasks.index(target)
        except ValueError:
            raise TaskNotFoundError(f"Target task '{before}' not in target list")
        target_list.tasks.insert(idx, task)
    elif after:
        target = find_task(task_file, after)
        if target is None:
            raise TaskNotFoundError(f"Target task not found: {after}")
        try:
            idx = target_list.tasks.index(target)
        except ValueError:
            raise TaskNotFoundError(f"Target task '{after}' not in target list")
        target_list.tasks.insert(idx + 1, task)
    else:
        target_list.tasks.append(task)

    return task


def find_task_list(task_file: TaskFile, task: Task) -> TaskList | None:
    """Find which list contains a task (top-level only)."""
    for task_list in task_file.lists:
        if task in task_list.tasks:
            return task_list
    return None


def link_dependency(
    task_file: TaskFile,
    query: str,
    depends_on: str,
) -> Task:
    """Add a dependency to a task."""
    task = find_task(task_file, query)
    if task is None:
        raise TaskNotFoundError(f"Task not found: {query}")

    # Verify dependency exists
    dep_task = find_task(task_file, depends_on)
    if dep_task is None:
        raise TaskNotFoundError(f"Dependency task not found: {depends_on}")

    # Check for circular dependency
    if would_create_cycle(task_file, task, dep_task):
        raise CircularDependencyError(f"Circular dependency: {query} -> {depends_on}")

    # Store as the query string (bookmark or title)
    task.metadata["depends"] = depends_on
    return task


def link_doc(
    task_file: TaskFile,
    query: str,
    doc_path: str,
) -> Task:
    """Add a doc reference to a task."""
    task = find_task(task_file, query)
    if task is None:
        raise TaskNotFoundError(f"Task not found: {query}")

    existing = task.metadata.get("docs", "")
    if existing:
        # Check for duplicates
        existing_docs = [d.strip() for d in existing.split(",")]
        if doc_path not in existing_docs:
            task.metadata["docs"] = f"{existing}, {doc_path}"
    else:
        task.metadata["docs"] = doc_path

    return task


def would_create_cycle(task_file: TaskFile, task: Task, dep: Task) -> bool:
    """Check if adding dep as dependency of task would create a cycle."""
    # Check if task is already a dependency of dep (direct or transitive)
    visited = set()

    def check(t: Task) -> bool:
        if t is task:
            return True
        if id(t) in visited:
            return False
        visited.add(id(t))

        if "depends" in t.metadata:
            dep_task = find_task(task_file, t.metadata["depends"])
            if dep_task and check(dep_task):
                return True
        return False

    return check(dep)
