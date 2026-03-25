# Quick Task

A markdown-based task management CLI for humans and AI agents.  Tasks live in
a plain-text `TASKS.md` file that you can edit by hand, commit to version
control, and manage with the `qt` command.

## Documentation

| Resource | What's inside |
|----------|---------------|
| **[Full Manual](docs/manual.md)** | Complete CLI reference, file format spec, behaviour rules, Python API, and agent integration guide |
| **[Quick Start](#quick-start)** | Five-minute intro — right below |
| `qt COMMAND --help` | Inline help for any command |

---

## Installation

```bash
pip install quick-task
```

## Quick Start

```bash
# Create a TASKS.md in the current directory
qt init                    # simple template
qt init --template kanban  # TODO / In Progress / Done lists

# Add tasks
qt add "Write tests"
qt add "Deploy" --list "Backlog"
qt add "Unit tests" --parent "Write tests"

# Work with tasks
qt list                    # show everything
qt list --status todo      # filter by status
qt start "Write tests"     # mark in-progress
qt done  "Write tests"     # mark done

# Reference by bookmark for reliability
qt add "Critical fix [#bug-42]"
qt done "#bug-42"
```

## Task Statuses

| Symbol | Status      | Command     |
|--------|-------------|-------------|
| `[ ]`  | Todo        | `qt reset`  |
| `[~]`  | In Progress | `qt start`  |
| `[x]`  | Done        | `qt done`   |
| `[-]`  | Cancelled   | `qt cancel` |
| `[?]`  | Blocked     | `qt block`  |
| `[>]`  | Deferred    | `qt defer`  |

## Command Overview

```
qt init   [--template T] [--force]                Create TASKS.md
qt list   [--status S] [--list L] [--json]        List / filter tasks
qt add    "Title" [--list L] [--parent P]          Add a task
qt start / done / block / defer / cancel / reset   Change status
qt show   "query" [--json]                         Show task detail
qt rename "query" "New title"                      Rename a task
qt remove "query"                                  Delete a task
qt move   "query" [--before B|--after A] [--list]  Reorder tasks
qt link   "query" [--depends D] [--doc URL]        Link tasks / docs
qt note   "query" "key: value"                     Add metadata
qt edit   ["query"]                                Open in $EDITOR
qt check  [--json]                                 Validate file
```

Use `qt COMMAND --help` for full options on any command.

→ **[Full manual — all commands, format spec, behaviour rules, and agent usage](docs/manual.md)**

## License

MIT
