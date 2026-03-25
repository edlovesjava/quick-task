# Quick Task — Full Manual

> **Quick Task (`qt`)** is a markdown-based task management CLI for humans and
> AI agents.  Tasks live in a plain-text `TASKS.md` file that you can edit by
> hand, commit to version control, and manage programmatically.

---

## Table of Contents

1. [Installation](#installation)
2. [File Format](#file-format)
   - [Basic Structure](#basic-structure)
   - [Task Statuses](#task-statuses)
   - [Subtasks & Hierarchy](#subtasks--hierarchy)
   - [Bookmarks](#bookmarks)
   - [Metadata](#metadata)
3. [File Discovery](#file-discovery)
4. [CLI Reference](#cli-reference)
   - [Global Options](#global-options)
   - [init](#init)
   - [list](#list)
   - [add](#add)
   - [Status Commands](#status-commands)
   - [show](#show)
   - [rename](#rename)
   - [remove](#remove)
   - [move](#move)
   - [link](#link)
   - [note](#note)
   - [edit](#edit)
   - [check](#check)
5. [Task Matching](#task-matching)
6. [Behaviour Rules](#behaviour-rules)
   - [Hierarchy Roll-up](#hierarchy-roll-up)
   - [Dependencies](#dependencies)
7. [Python API](#python-api)
8. [Agent Integration](#agent-integration)
9. [Project Structure](#project-structure)

---

## Installation

```bash
pip install quick-task
```

Install from source (development mode):

```bash
git clone <repo-url>
cd quick-task
pip install -e ".[dev]"
```

---

## File Format

Quick Task parses standard Markdown files.  The default file name is
`TASKS.md`, but any `.md` file works when supplied with `-f`.

### Basic Structure

```markdown
# My Project

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

Key points:

- A **top-level heading** (`#`) is optional and ignored by the parser.
- **Second-level headings** (`##`) define named **task lists**.
- **Checkbox list items** (`- [ ]`, `- [x]`, …) are tasks.
- Everything else is treated as surrounding prose and is preserved as-is.

### Task Statuses

| Syntax | Status      | CLI command to set |
|--------|-------------|--------------------|
| `[ ]`  | Todo        | `qt reset`         |
| `[~]`  | In Progress | `qt start`         |
| `[x]`  | Done        | `qt done`          |
| `[-]`  | Cancelled   | `qt cancel`        |
| `[?]`  | Blocked     | `qt block`         |
| `[>]`  | Deferred    | `qt defer`         |

### Subtasks & Hierarchy

Indent child tasks by **4 spaces** per level:

```markdown
- [ ] Parent task
    - [ ] Child task
        - [ ] Grandchild task
```

Rules:

- When **all** children reach `done`, the parent is automatically promoted to
  `done`.
- Marking a **parent done** cascades `done` to all incomplete children.
- Marking a **parent cancelled** cascades `cancelled` to all children.
- **Blocking** a parent does *not* cascade to children.

There is no enforced depth limit, but deeply nested trees can be hard to read.

### Bookmarks

Append `[#slug]` to a list header or task title to create a stable reference:

```markdown
## Sprint 1 [#sprint-1]

- [ ] Fix login redirect [#bug-42]
```

Bookmarks must be unique within a file.  Use them wherever you need a
deterministic reference—scripts, agent prompts, `depends:` fields, etc.

```bash
qt done "#bug-42"       # exact, always unambiguous
qt start "#sprint-1"    # reference the whole list (where applicable)
```

Run `qt check` to detect duplicate bookmarks.

### Metadata

Add indented `key: value` lines directly below a task item (before any
subtasks):

```markdown
- [ ] Deploy to production [#deploy]
    depends: #staging-tests
    due: 2024-03-15
    owner: alice
    docs: docs/runbook.md
```

Metadata lines are preserved verbatim by the writer; `qt` itself only
understands `depends:` and `docs:` for its dependency and link features.
All other keys are stored as freeform annotations.

---

## File Discovery

When you run `qt` without `-f`, it searches for `TASKS.md` starting in the
current working directory and walking **upward** through parent directories
until it finds a match.  This means you can run `qt` from any subdirectory of
your project.

Override at any time with the `-f` / `--file` flag:

```bash
qt -f ~/tasks/personal.md list
qt -f ./sprint-3.md add "New task"
```

---

## CLI Reference

### Global Options

```
qt [OPTIONS] COMMAND [ARGS]...

Options:
  -f, --file PATH   Task file to use (default: auto-discovered TASKS.md)
  --version         Show version and exit
  --help            Show help and exit
```

These options must come **before** the subcommand name.

---

### init

Create a new `TASKS.md` (or another file) from a template.

```bash
qt init                    # Simple template — one list, one example task
qt init --template kanban  # Kanban template — TODO / In Progress / Done
qt init --force            # Overwrite an existing file
```

Templates:

| Name     | Lists created                        |
|----------|--------------------------------------|
| `simple` | `Tasks`                              |
| `kanban` | `TODO`, `In Progress`, `Done` (with bookmarks) |

---

### list

Show tasks, optionally filtered.

```bash
qt list                          # All tasks in all lists
qt list --status todo            # Only tasks with the given status
qt list --status in-progress
qt list --status done
qt list --status blocked
qt list --status deferred
qt list --status cancelled
qt list --list "Sprint 1"        # Only tasks in a named list
qt list --json                   # Structured JSON output (for scripts/agents)
qt list --verbose                # Include metadata lines
```

Multiple filters can be combined:

```bash
qt list --status todo --list "Backlog"
```

---

### add

Create a new task.

```bash
qt add "Task title"                       # Append to the first list
qt add "Task title" --list "Backlog"      # Append to a named list
qt add "Subtask title" --parent "auth"    # Fuzzy-match parent
qt add "Subtask title" --parent "#auth"   # Exact bookmark match
```

The new task is always appended at the **bottom** of the target list (or
parent's children).  Use `qt move` afterwards to reorder.

---

### Status Commands

Each command flips a task's status character in place.

```bash
qt start  "query"          # [~] In Progress
qt done   "query"          # [x] Done  (cascades to children)
qt done   "query" --force  # [x] Done  even if dependencies are incomplete
qt block  "query"          # [?] Blocked
qt defer  "query"          # [>] Deferred
qt cancel "query"          # [-] Cancelled  (cascades to children)
qt reset  "query"          # [ ] Todo  (un-done / un-cancel / etc.)
```

`done` and `cancel` cascade to children (see
[Hierarchy Roll-up](#hierarchy-roll-up)).

`qt done` warns if any declared `depends:` dependency is still incomplete.
Use `--force` to override the warning and mark the task done anyway.

---

### show

Display full details of a single task.

```bash
qt show "query"        # Human-readable detail view
qt show "query" --json # JSON detail (for scripts/agents)
```

Outputs: title, status, bookmark, list, metadata, subtask tree, and any
linked dependencies or docs.

---

### rename

Change a task's title without altering its bookmark or status.

```bash
qt rename "old title" "New title"
qt rename "#bug-42"   "Fix login redirect on Safari"
```

---

### remove

Permanently delete a task (and all its subtasks) from the file.

```bash
qt remove "query"
qt remove "#bug-42"
```

There is no undo — commit your file to version control first.

---

### move

Reorder a task within a list, or move it to a different list.

```bash
qt move "task" --before "other task"        # Immediately before another task
qt move "task" --after  "other task"        # Immediately after another task
qt move "task" --list   "Done"              # Move to another list
qt move "task" --after  "x" --list "Done"   # Move + reorder in one step
```

`--before` and `--after` accept the same fuzzy/bookmark queries as all other
commands.

---

### link

Attach dependency or documentation links to a task.

```bash
qt link "Task B" --depends "Task A"         # Task B depends on Task A
qt link "Task B" --depends "#task-a"        # Same, via bookmark
qt link "Deploy" --doc "docs/runbook.md"    # Attach a doc reference
```

These write `depends:` and `docs:` metadata lines under the task.  Multiple
`--depends` and `--doc` flags are accepted in one command.

---

### note

Add or update a freeform metadata key under a task.

```bash
qt note "Deploy" "owner: alice"
qt note "#deploy" "due: 2024-03-15"
```

If the key already exists its value is replaced; otherwise the line is
appended.

---

### edit

Open the raw task file (or jump to a specific task) in `$EDITOR`.

```bash
qt edit              # Open full file
qt edit "query"      # Open file with cursor on matched task (if editor supports it)
```

Requires `$EDITOR` to be set (e.g. `export EDITOR=vim`).

---

### check

Validate the task file for syntax errors, duplicate bookmarks, and bad
references.

```bash
qt check            # Human-readable report
qt check --json     # JSON report (for CI)
```

Exits with code `0` on success, `1` on any error.  Wire this into your CI
pipeline to catch malformed task files early.

---

## Task Matching

When you pass a query string to most commands, `qt` resolves it as follows:

1. **Bookmark** — if the query starts with `#`, perform an exact lookup (e.g.
   `"#bug-42"`).  This is always unambiguous and preferred in scripts.
2. **Fuzzy title** — case-insensitive substring match against all task titles.
   - Exactly one match → proceed.
   - Zero matches → error: task not found.
   - Multiple matches → error: ambiguous query; list the matching titles and
     ask the user to be more specific (or use a bookmark).

---

## Behaviour Rules

### Hierarchy Roll-up

| Action on parent          | Effect on children                     |
|---------------------------|----------------------------------------|
| All children → done       | Parent auto-promoted to done           |
| `qt done` on parent       | All incomplete children → done         |
| `qt cancel` on parent     | All children → cancelled               |
| `qt block` on parent      | Children **not** affected              |
| `qt start` on parent      | Children **not** affected              |

### Dependencies

Tasks can declare `depends:` metadata referencing other tasks by bookmark or
fuzzy title.

- `qt list` surfaces tasks whose dependencies are **not yet complete** (these
  are effectively blocked even if not marked `[?]`).
- `qt done` **warns** if any declared dependency is still incomplete.
  Pass `--force` to override the warning and mark done anyway.
- Circular dependencies are detected at parse time and reported as errors by
  `qt check`.

---

## Python API

```python
from quick_task.api import (
    load_file,
    get_task,
    list_tasks,
    add_task,
    update_status,
    TaskStatus,
)

# Load a task file
tasks = load_file("TASKS.md")

# Retrieve a specific task by bookmark
task = get_task(tasks, "#important")

# List tasks with filters
todo_items = list_tasks(tasks, status=TaskStatus.TODO, flat=True)

# Add a new task
add_task(tasks, "New task", list_name="My Tasks")

# Change status and write back to disk
update_status(tasks, "#important", TaskStatus.DONE, "TASKS.md")
```

The API surface mirrors the CLI exactly — every CLI command has a
corresponding function.  This lets other tools (e.g. editor plugins, web
dashboards, or AI agents) drive `qt` programmatically without shelling out.

---

## Agent Integration

AI agents use the same CLI interface as human users.  The conventions below
make agent use reliable:

| Recommendation | Reason |
|---|---|
| Always use bookmarks (`#slug`) in commands | Eliminates fuzzy-match ambiguity |
| Use `--json` when reading output | Stable structured format; doesn't break on terminal formatting changes |
| Run `qt check` after bulk edits | Catches duplicate bookmarks and bad references immediately |
| Prefer `qt add` over hand-editing | Writer guarantees valid syntax |
| Store the file in version control | Easy rollback if an agent makes a mistake |

Example agent session:

```bash
# What's left to do?
qt list --status todo --json

# Start the next task
qt start "#auth"

# Add a subtask discovered mid-implementation
qt add "Handle token expiry edge case" --parent "#auth"

# Record a design decision
qt note "#auth" "approach: JWT RS256 — see docs/auth-spec.md"

# Finish up
qt done "#auth"
```

> **Tip for agent prompts:** include the bookmark of the current task in every
> prompt so the agent can reference it unambiguously.  E.g. "You are working
> on `#auth`.  Use `qt show "#auth"` to read its full state before acting."

---

## Project Structure

```
quick-task/
├── pyproject.toml
├── README.md
├── docs/
│   ├── manual.md               # ← this file
│   └── plans/
│       └── 2026-02-04-qt-cli-design.md
├── src/
│   └── quick_task/
│       ├── __init__.py
│       ├── api.py              # Public Python API
│       ├── cli.py              # Click-based CLI entry-point
│       ├── parser.py           # Markdown → model
│       ├── writer.py           # Model → Markdown
│       ├── models.py           # Task, TaskList dataclasses
│       ├── matcher.py          # Fuzzy + bookmark matching
│       └── operations.py       # Business logic (status changes, move, …)
└── tests/
    ├── test_parser.py
    ├── test_writer.py
    ├── test_operations.py
    └── fixtures/
```

### Runtime Dependencies

| Package | Purpose |
|---------|---------|
| `click` | CLI framework & argument parsing |
| `rich`  | Pretty terminal output (tables, colours, trees) |
