"""Fuzzy matching for task titles."""

from quick_task.models import Task, TaskList, TaskFile


class AmbiguousMatchError(Exception):
    """Raised when a query matches multiple tasks."""

    def __init__(self, query: str, matches: list[Task]):
        self.query = query
        self.matches = matches
        titles = [f"  - {t.title}" + (f" [#{t.bookmark}]" if t.bookmark else "") for t in matches]
        msg = f"Ambiguous match for '{query}', {len(matches)} tasks matched:\n" + "\n".join(titles)
        msg += "\nUse a bookmark (#name) for an exact match."
        super().__init__(msg)


def find_task(task_file: TaskFile, query: str) -> Task | None:
    """Find a single task matching the query. Returns None if no match, raises AmbiguousMatchError if multiple."""
    matches = find_tasks(task_file, query)
    if len(matches) == 1:
        return matches[0]
    if len(matches) > 1:
        raise AmbiguousMatchError(query, matches)
    return None


def find_tasks(task_file: TaskFile, query: str) -> list[Task]:
    """Find all tasks matching the query."""
    query = query.strip()

    # Bookmark lookup (exact match)
    if query.startswith("#"):
        bookmark = query[1:]
        return [t for t in all_tasks(task_file) if t.bookmark == bookmark]

    # Fuzzy title match
    query_lower = query.lower()
    matches = []
    for task in all_tasks(task_file):
        if query_lower in task.title.lower():
            matches.append(task)

    return matches


def all_tasks(task_file: TaskFile) -> list[Task]:
    """Get all tasks from a task file, flattened."""
    tasks = []
    for task_list in task_file.lists:
        tasks.extend(collect_tasks(task_list.tasks))
    return tasks


def collect_tasks(tasks: list[Task]) -> list[Task]:
    """Recursively collect all tasks including children."""
    result = []
    for task in tasks:
        result.append(task)
        result.extend(collect_tasks(task.children))
    return result
