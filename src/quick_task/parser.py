"""Markdown parser for task files."""

import re
from pathlib import Path

from quick_task.models import Task, TaskList, TaskFile, TaskStatus


HEADER_PATTERN = re.compile(r"^(#{1,6})\s+(.+?)(?:\s+\[#([\w-]+)\])?\s*$")
TASK_PATTERN = re.compile(r"^(\s*)- \[(.)\]\s+(.+?)(?:\s+\[#([\w-]+)\])?\s*$")


def parse_file(path: str | Path) -> TaskFile:
    """Parse a markdown file into a TaskFile."""
    path = Path(path)
    content = path.read_text()
    return parse_content(content, path)


def parse_content(content: str, path: str | Path = "TASKS.md") -> TaskFile:
    """Parse markdown content into a TaskFile."""
    lines = content.split("\n")
    lists: list[TaskList] = []
    current_list: TaskList | None = None

    for line in lines:
        # Check for header
        header_match = HEADER_PATTERN.match(line)
        if header_match:
            name = header_match.group(2)
            bookmark = header_match.group(3)
            current_list = TaskList(name=name, bookmark=bookmark)
            lists.append(current_list)
            continue

        # Check for task
        task_match = TASK_PATTERN.match(line)
        if task_match and current_list is not None:
            indent = len(task_match.group(1))
            symbol = task_match.group(2)
            title = task_match.group(3)
            bookmark = task_match.group(4)

            status = TaskStatus.from_symbol(symbol)
            task = Task(title=title, status=status, bookmark=bookmark)

            if indent == 0:
                current_list.tasks.append(task)

    return TaskFile(path=path, lists=lists)
