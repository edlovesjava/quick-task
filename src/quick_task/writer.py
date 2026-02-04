"""Markdown writer for task files."""

from pathlib import Path

from quick_task.models import Task, TaskList, TaskFile


def write_file(task_file: TaskFile) -> None:
    """Write a TaskFile back to its markdown file."""
    path = Path(task_file.path)
    content = write_content(task_file)
    path.write_text(content)


def write_content(task_file: TaskFile) -> str:
    """Convert a TaskFile to markdown content."""
    lines: list[str] = []

    for task_list in task_file.lists:
        lines.append(format_list_header(task_list))
        lines.append("")
        for task in task_list.tasks:
            lines.extend(format_task(task, indent=0))

    return "\n".join(lines) + "\n"


def format_list_header(task_list: TaskList) -> str:
    """Format a task list header."""
    header = f"## {task_list.name}"
    if task_list.bookmark:
        header += f" [#{task_list.bookmark}]"
    return header


def format_task(task: Task, indent: int = 0) -> list[str]:
    """Format a task and its children as markdown lines."""
    lines: list[str] = []
    prefix = "    " * indent

    # Task line
    line = f"{prefix}- [{task.status.symbol}] {task.title}"
    if task.bookmark:
        line += f" [#{task.bookmark}]"
    lines.append(line)

    # Metadata
    for key, value in task.metadata.items():
        lines.append(f"{prefix}    {key}: {value}")

    # Children
    for child in task.children:
        lines.extend(format_task(child, indent + 1))

    return lines
