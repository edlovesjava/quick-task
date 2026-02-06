"""Task file validation."""

import re
from dataclasses import dataclass
from pathlib import Path

from quick_task.parser import HEADER_PATTERN, TASK_PATTERN, METADATA_PATTERN
from quick_task.models import TaskStatus


# Near-miss patterns: lines that look like they're trying to be tasks but don't parse
NEAR_MISS_TASK = re.compile(r"^\s*-\s*\[.*\]")  # has "- [" but doesn't match TASK_PATTERN
VALID_SYMBOLS = {s.value for s in TaskStatus}


@dataclass
class Issue:
    """A validation issue found in the task file."""

    line: int
    level: str  # "error" or "warning"
    code: str
    message: str


def check_file(path: str | Path) -> list[Issue]:
    """Validate a task file and return a list of issues."""
    path = Path(path)
    content = path.read_text()
    return check_content(content)


def check_content(content: str) -> list[Issue]:
    """Validate task file content and return a list of issues."""
    lines = content.split("\n")
    issues: list[Issue] = []
    current_task_indent: int | None = None
    has_current_task = False
    bookmarks: dict[str, int] = {}  # bookmark -> line number
    all_titles: set[str] = set()
    depends_refs: list[tuple[int, str]] = []  # (line, depends_value)

    for i, line in enumerate(lines, 1):
        # Skip blank lines
        if not line.strip():
            has_current_task = False
            current_task_indent = None
            continue

        # Check for header
        if HEADER_PATTERN.match(line):
            header_match = HEADER_PATTERN.match(line)
            bookmark = header_match.group(3)
            if bookmark:
                if bookmark in bookmarks:
                    issues.append(Issue(
                        line=i, level="error", code="duplicate-bookmark",
                        message=f"Duplicate bookmark '#{bookmark}' (first used on line {bookmarks[bookmark]})",
                    ))
                else:
                    bookmarks[bookmark] = i
            has_current_task = False
            current_task_indent = None
            continue

        # Check for valid task
        task_match = TASK_PATTERN.match(line)
        if task_match:
            symbol = task_match.group(2)
            bookmark = task_match.group(4)

            # Check for unknown status symbol
            if symbol not in VALID_SYMBOLS:
                issues.append(Issue(
                    line=i, level="error", code="unknown-status",
                    message=f"Unknown status symbol '{symbol}' (valid: {' '.join(VALID_SYMBOLS)})",
                ))

            # Check for duplicate bookmark
            if bookmark:
                if bookmark in bookmarks:
                    issues.append(Issue(
                        line=i, level="error", code="duplicate-bookmark",
                        message=f"Duplicate bookmark '#{bookmark}' (first used on line {bookmarks[bookmark]})",
                    ))
                else:
                    bookmarks[bookmark] = i

            title = task_match.group(3)
            # Strip bookmark from title if present
            title_bookmark = task_match.group(4)
            all_titles.add(title)

            has_current_task = True
            current_task_indent = len(task_match.group(1))
            continue

        # Check for near-miss task lines
        if NEAR_MISS_TASK.match(line):
            issues.append(Issue(
                line=i, level="error", code="malformed-task",
                message=f"Malformed task line (expected '- [x] title'): {line.strip()}",
            ))
            continue

        # Check for metadata
        metadata_match = METADATA_PATTERN.match(line)
        if metadata_match:
            if not has_current_task:
                issues.append(Issue(
                    line=i, level="warning", code="orphaned-metadata",
                    message=f"Metadata not attached to any task: {line.strip()}",
                ))
            else:
                key = metadata_match.group(1)
                value = metadata_match.group(2).strip()
                if key == "depends":
                    depends_refs.append((i, value))
            continue

    # Validate depends references using data collected in first pass
    all_bookmarks = set(bookmarks.keys())
    for dep_line, dep_value in depends_refs:
        if dep_value.startswith("#"):
            ref_bookmark = dep_value[1:]
            if ref_bookmark not in all_bookmarks:
                issues.append(Issue(
                    line=dep_line, level="error", code="broken-depends",
                    message=f"Dependency '#{ref_bookmark}' not found (no task with that bookmark)",
                ))
        else:
            matching = [t for t in all_titles if dep_value.lower() in t.lower()]
            if not matching:
                issues.append(Issue(
                    line=dep_line, level="warning", code="broken-depends",
                    message=f"Dependency '{dep_value}' may not match any task",
                ))

    return issues
