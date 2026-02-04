"""File discovery for task files."""

from pathlib import Path


DEFAULT_FILENAME = "TASKS.md"


def find_task_file(
    start_dir: str | Path | None = None,
    explicit_file: str | Path | None = None,
) -> Path | None:
    """Find a task file, walking up directories if needed."""
    if explicit_file:
        path = Path(explicit_file)
        return path if path.exists() else None

    start = Path(start_dir) if start_dir else Path.cwd()
    current = start.resolve()

    while True:
        candidate = current / DEFAULT_FILENAME
        if candidate.exists():
            return candidate

        parent = current.parent
        if parent == current:
            # Reached root
            return None
        current = parent
