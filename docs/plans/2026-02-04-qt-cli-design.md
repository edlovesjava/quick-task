# Quick Task (qt) CLI Design

A markdown-based task management CLI for humans and agents.

## Overview

`qt` manages tasks stored in markdown files. The format is readable and editable by hand while being reliably parseable by the CLI. Both humans and AI agents use the same interface.

## Markdown Format

```markdown
# Project Tasks

## Backlog [#backlog]

- [ ] Design authentication system [#auth]
    depends: Set up database
    docs: docs/auth-spec.md
- [ ] Set up database [#db]
- [~] Build user registration
    - [x] Create registration form
    - [ ] Add email validation
    - [ ] Send welcome email

## Done

- [x] Project setup
- [-] Cancelled feature idea
```

### Task Statuses

| Syntax | Status |
|--------|--------|
| `[ ]` | Todo |
| `[~]` | In-progress |
| `[x]` | Done |
| `[-]` | Cancelled |
| `[?]` | Blocked |
| `[>]` | Deferred |

### Structure Elements

- **Headers** (`##`) define named task lists
- **Bookmarks** `[#name]` provide stable references for linking
- **Metadata** indented lines below a task (key: value format)
- **Hierarchy** nested tasks via markdown indentation
- **Priority** position in list (top = highest priority)

## CLI Commands

### Adding Tasks

```bash
qt add "Task title"                       # Add to default list
qt add "Task title" --file=sprint.md      # Specific file
qt add "Task title" --list=Backlog        # Specific list
qt add "Subtask" --parent="Parent task"   # Add as child
```

### Updating Status

```bash
qt done "Task title"      # Mark complete [x]
qt start "Task title"     # Mark in-progress [~]
qt block "Task title"     # Mark blocked [?]
qt defer "Task title"     # Mark deferred [>]
qt cancel "Task title"    # Mark cancelled [-]
qt reset "Task title"     # Back to todo [ ]
```

### Viewing Tasks

```bash
qt list                     # Show all tasks
qt list --status=todo       # Filter by status
qt list --list=Backlog      # Filter by list name
qt list --json              # Structured output for agents
```

### Organizing

```bash
qt move "Task" --before="Other task"    # Reorder by priority
qt move "Task" --after="Other task"
qt move "Task" --list=Done              # Move between lists
```

### Dependencies & Metadata

```bash
qt link "Task B" --depends="Task A"     # Add dependency
qt note "Task" "Additional info"        # Add/update metadata
qt edit "Task"                          # Open in $EDITOR
```

## Behavior Rules

### Fuzzy Matching

- Case-insensitive partial matching on task titles
- Multiple matches prompt for disambiguation
- Bookmarks (`#auth`) are exact and take precedence

### Hierarchy Rollup

- Completing all children auto-completes parent
- Completing parent marks all incomplete children as done
- Cancelling parent cancels all children
- Blocking parent doesn't cascade

### Dependencies

- `qt list` shows tasks with incomplete dependencies
- `qt done` warns if dependencies incomplete (override with `--force`)
- Circular dependencies detected and rejected

### File Discovery

- Default: `TASKS.md` in current directory
- Walks up directory tree if not found
- `--file` flag for explicit targeting
- Default list: first list in file

## Project Structure

```
quick-task/
├── pyproject.toml
├── README.md
├── src/
│   └── quick_task/
│       ├── __init__.py
│       ├── cli.py          # Click-based CLI
│       ├── parser.py       # Markdown parsing
│       ├── writer.py       # Markdown writing
│       ├── models.py       # Task, TaskList dataclasses
│       ├── matcher.py      # Fuzzy matching
│       └── operations.py   # Business logic
└── tests/
    ├── test_parser.py
    ├── test_writer.py
    ├── test_operations.py
    └── fixtures/
```

### Dependencies

- `click` - CLI framework
- `rich` - Pretty terminal output

## Agent Integration

Agents use the same CLI commands:

```bash
qt add "Fix null check in auth handler" --list=Bugs
qt done "Implement login form"
qt list --status=todo --json
qt note "Auth system" "Using JWT per docs/auth.md"
```

The `--json` flag provides structured output for programmatic parsing.
