# Usage Guide

## Initializing a Task File

Create a new `TASKS.md` file using `qt init`:

```bash
qt init                    # Simple template with one list
qt init --template kanban  # Kanban-style with TODO/In Progress/Done
qt init --force            # Overwrite existing file
```

**Templates:**

- `simple` (default): Single "Tasks" list with one example task
- `kanban`: Three lists (TODO, In Progress, Done) with bookmarks

## File Format

Quick Task uses markdown files with a specific format. By default, it looks for `TASKS.md` in the current directory or any parent directory.

### Basic Structure

```markdown
## Project Tasks [#project]

- [ ] Implement feature A [#feature-a]
    - [ ] Design API
    - [ ] Write tests
    - [ ] Implement
- [~] Review documentation
- [x] Set up CI/CD
```

### Headers

Headers (`##`) define task lists. Add a bookmark for stable references:

```markdown
## Sprint 1 [#sprint-1]
## Backlog [#backlog]
```

### Tasks

Tasks are checkbox list items. The character inside brackets indicates status:

```markdown
- [ ] TODO - not started
- [~] In progress - actively working
- [x] Done - completed
- [-] Cancelled - won't do
- [?] Blocked - waiting on something
- [>] Deferred - postponed
```

### Subtasks

Indent with 4 spaces to create subtasks:

```markdown
- [ ] Parent task
    - [ ] Child task
        - [ ] Grandchild task
```

When all children are marked done, the parent automatically completes.

### Bookmarks

Add `[#name]` to reference tasks by stable ID:

```markdown
- [ ] Critical fix [#bug-123]
```

Reference in CLI: `qt done "#bug-123"`

### Metadata

Add key-value pairs below a task:

```markdown
- [ ] Deploy to production [#deploy]
    depends: #staging-tests
    due: 2024-03-15
```

## CLI Reference

### Global Options

```bash
qt --help           # Show help
qt --version        # Show version
qt -f FILE COMMAND  # Use specific file instead of TASKS.md
```

### Listing Tasks

```bash
qt list                      # All tasks
qt list --status todo        # Filter by status
qt list --status in-progress
qt list --status done
qt list --status blocked
qt list --status deferred
qt list --status cancelled
qt list --list "Sprint 1"    # Filter by list name
qt list --json               # JSON output for scripting
```

### Adding Tasks

```bash
qt add "Task title"                    # Add to first list
qt add "Task title" --list "Backlog"   # Add to specific list
qt add "Subtask" --parent "Parent"     # Add as subtask
qt add "Subtask" --parent "#bookmark"  # Add under bookmarked task
```

### Changing Status

Each status has a dedicated command:

```bash
qt start "task"    # Mark as in-progress [~]
qt done "task"     # Mark as done [x]
qt block "task"    # Mark as blocked [?]
qt defer "task"    # Mark as deferred [>]
qt cancel "task"   # Mark as cancelled [-]
qt reset "task"    # Reset to TODO [ ]
```

Status changes cascade to children for `done` and `cancel`.

### Moving Tasks

```bash
qt move "task" --before "other"     # Move before another task
qt move "task" --after "other"      # Move after another task
qt move "task" --list "Backlog"     # Move to another list
qt move "task" --after "x" --list "Done"  # Combine options
```

### Task Matching

Tasks are matched by:

1. **Bookmark** (exact): `#bookmark-name`
2. **Title** (fuzzy): partial case-insensitive match

If multiple tasks match a fuzzy query, the command fails. Use bookmarks for precision.

## Examples

### Project Setup

```bash
# Create kanban-style task file
qt init --template kanban

# Add tasks
qt add "Set up project structure" --list "TODO"
qt add "Write README" --list "TODO"
qt add "Add tests" --list "TODO"
```

### Daily Workflow

```bash
# Start working on a task
qt start "project structure"

# Check current status
qt list --status in-progress

# Mark complete and move to Done list
qt done "project structure"
qt move "project structure" --list "Done"
```

### Subtask Management

```bash
# Add parent task
qt add "Implement auth" --list "TODO"

# Add subtasks
qt add "Design API" --parent "auth"
qt add "Write tests" --parent "auth"
qt add "Implement handlers" --parent "auth"

# Complete subtasks (parent auto-completes when all children done)
qt done "Design API"
qt done "Write tests"
qt done "Implement handlers"  # Parent also marked done
```

### JSON Output for Scripts

```bash
# Get todo items as JSON
qt list --status todo --json

# Example output:
# [
#   {
#     "title": "Write tests",
#     "status": "todo",
#     "list": "TODO",
#     "bookmark": null
#   }
# ]
```

## File Discovery

Quick Task searches for `TASKS.md` starting from the current directory and walking up to parent directories. This lets you run `qt` from any subdirectory of your project.

Override with `-f`:

```bash
qt -f ~/tasks/personal.md list
qt -f ./sprint-3.md add "New task"
```
