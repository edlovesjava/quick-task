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


@dataclass
class Task:
    """A single task with optional children and metadata."""

    title: str
    status: TaskStatus
    bookmark: str | None = None
    children: list["Task"] = field(default_factory=list)
    metadata: dict[str, str] = field(default_factory=dict)


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
