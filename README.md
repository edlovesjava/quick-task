# Quick Task

A markdown-based task management CLI. Keeps your task list in a human-readable `TASKS.md` file that can be edited by hand or managed via the `qt` command.

## Features

- **Markdown-native**: Tasks stored as checkbox lists in markdown
- **Multiple statuses**: TODO, in-progress, done, cancelled, blocked, deferred
- **Nested tasks**: Subtasks via indentation with automatic rollup
- **Bookmarks**: Reference tasks by `[#bookmark]` for stable identification
- **Fuzzy matching**: Find tasks by partial title or exact bookmark
- **File discovery**: Walks up directories to find `TASKS.md`
- **Human + agent friendly**: Edit by hand or via CLI

## Installation

```bash
pip install quick-task
```

Or install from source:

```bash
pip install -e .
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
qt list              # Show all tasks
qt add "New task"    # Add a task
qt done "First"      # Mark matching task done
qt start "#important" # Start by bookmark
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

## Documentation

See [USAGE.md](USAGE.md) for detailed usage instructions.

## License

MIT
