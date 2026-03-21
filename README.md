# Quick Task

A markdown-based task management CLI. Keeps your task list in a human-readable `TASKS.md` file that can be edited by hand or managed via the `qt` command.

## Features

- **Markdown-native**: Tasks stored as checkbox lists in markdown
- **Multiple statuses**: TODO, in-progress, done, cancelled, blocked, deferred
- **Nested tasks**: Subtasks via indentation with automatic rollup
- **Bookmarks**: Reference tasks by `[#bookmark]` for stable identification
- **Fuzzy matching**: Find tasks by partial title or exact bookmark
- **Dependencies & docs**: Link tasks to each other or to documentation
- **Metadata**: Attach key-value pairs to any task
- **File discovery**: Walks up directories to find `TASKS.md`
- **Validation**: Check task files for syntax errors and duplicate bookmarks
- **Python API**: Use programmatically from other tools
- **Human + agent friendly**: Edit by hand or via CLI

## Installation

```bash
pip install quick-task
```

Or install from source:

```bash
pip install -e ".[dev]"
```

## Quick Start

Create a `TASKS.md` file:

```markdown
## My Tasks

- [ ] First task
- [ ] Second task [#important]
    - [ ] Subtask
```

Or use `qt init` to create one:

```bash
qt init                    # Create simple TASKS.md
qt init --template kanban  # Create kanban-style file
```

Then use the CLI:

```bash
qt list                    # Show all tasks
qt add "New task"          # Add a task
qt done "First"            # Mark matching task done
qt start "#important"      # Start by bookmark
qt show "#important"       # Show task details
qt check                   # Validate task file
```

## Task Statuses

| Symbol | Status      | Command   |
|--------|-------------|-----------|
| `[ ]`  | TODO        | `reset`   |
| `[~]`  | In Progress | `start`   |
| `[x]`  | Done        | `done`    |
| `[-]`  | Cancelled   | `cancel`  |
| `[?]`  | Blocked     | `block`   |
| `[>]`  | Deferred    | `defer`   |

## Commands

```
qt list [--status S] [--list L] [--json] [--verbose]   List/filter tasks
qt add "Title" [--list L] [--parent P]                  Add a task
qt done/start/block/defer/cancel/reset "Query"          Change status
qt show "Query" [--json]                                Show task detail
qt rename "Query" "New title"                           Rename a task
qt remove "Query"                                       Delete a task
qt move "Query" [--before B] [--after A] [--list L]     Reorder tasks
qt link "Query" [--depends D] [--doc URL]               Link tasks/docs
qt note "Query" "Text"                                  Add metadata
qt edit ["Query"]                                       Open in $EDITOR
qt check [--json]                                       Validate syntax
qt init [--template T]                                  Create TASKS.md
```

## Python API

```python
from quick_task.api import load_file, get_task, list_tasks, add_task, update_status

# Load a task file
tasks = load_file("TASKS.md")

# Find a task by bookmark
task = get_task(tasks, "#important")

# List tasks with filters
todo = list_tasks(tasks, status=TaskStatus.TODO, flat=True)

# Add a task
add_task(tasks, "New task", list_name="My Tasks")

# Update status
update_status(tasks, "#important", TaskStatus.DONE, "TASKS.md")
```

## Documentation

See [USAGE.md](USAGE.md) for detailed usage instructions.

## License

MIT
