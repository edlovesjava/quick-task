"""Data models for Quick Task."""

from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path


class TaskStatus(Enum):
    """Task status with markdown checkbox symbols."""

    TODO = " "
    IN_PROGRESS = "~"
    DONE = "x"
    CANCELLED = "-"
    BLOCKED = "?"
    DEFERRED = ">"

    @property
    def symbol(self) -> str:
        return self.value

    @classmethod
    def from_symbol(cls, symbol: str) -> "TaskStatus":
        for status in cls:
            if status.value == symbol:
                return status
        raise ValueError(f"Unknown status symbol: {symbol}")


# First-class metadata field names
METADATA_ASSIGNEE = "assignee"
METADATA_PRIORITY = "priority"
METADATA_CREATED = "created"
METADATA_UPDATED = "updated"

# Valid priority values (ordered lowest → highest)
PRIORITY_LEVELS = ("low", "medium", "high", "critical")


@dataclass
class Task:
    """A single task with optional children and metadata.

    Agent-oriented first-class fields (assignee, priority, created, updated)
    are stored in ``metadata`` so they round-trip through the markdown
    parser/writer without any format changes.  Convenience properties expose
    them as typed attributes.
    """

    title: str
    status: TaskStatus
    bookmark: str | None = None
    children: list["Task"] = field(default_factory=list)
    metadata: dict[str, str] = field(default_factory=dict)

    # ------------------------------------------------------------------
    # First-class agent-oriented properties
    # ------------------------------------------------------------------

    @property
    def assignee(self) -> str | None:
        """Who this task is assigned to (e.g. ``@builder``)."""
        return self.metadata.get(METADATA_ASSIGNEE)

    @assignee.setter
    def assignee(self, value: str | None) -> None:
        if value is None:
            self.metadata.pop(METADATA_ASSIGNEE, None)
        else:
            self.metadata[METADATA_ASSIGNEE] = value

    @property
    def priority(self) -> str | None:
        """Task priority: ``low``, ``medium``, ``high``, or ``critical``."""
        return self.metadata.get(METADATA_PRIORITY)

    @priority.setter
    def priority(self, value: str | None) -> None:
        if value is None:
            self.metadata.pop(METADATA_PRIORITY, None)
        else:
            if value not in PRIORITY_LEVELS:
                raise ValueError(
                    f"Invalid priority {value!r}. Must be one of: {', '.join(PRIORITY_LEVELS)}"
                )
            self.metadata[METADATA_PRIORITY] = value

    @property
    def created(self) -> str | None:
        """ISO-8601 creation timestamp string."""
        return self.metadata.get(METADATA_CREATED)

    @created.setter
    def created(self, value: str | None) -> None:
        if value is None:
            self.metadata.pop(METADATA_CREATED, None)
        else:
            self.metadata[METADATA_CREATED] = value

    @property
    def updated(self) -> str | None:
        """ISO-8601 last-updated timestamp string."""
        return self.metadata.get(METADATA_UPDATED)

    @updated.setter
    def updated(self, value: str | None) -> None:
        if value is None:
            self.metadata.pop(METADATA_UPDATED, None)
        else:
            self.metadata[METADATA_UPDATED] = value


@dataclass
class TaskList:
    """A named list of tasks (corresponds to a markdown header)."""

    name: str
    tasks: list[Task] = field(default_factory=list)
    bookmark: str | None = None


@dataclass
class TaskFile:
    """A markdown file containing one or more task lists."""

    path: str | Path
    lists: list[TaskList] = field(default_factory=list)
