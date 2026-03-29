## Genesis API [#genesis-api]

- [x] Python API module (spec §8.1) [#qt-api]
    docs: docs/plans/2026-03-20-python-api-design.md
    - [x] Create src/quick_task/api.py public module [#qt-api-module]
    - [x] load_file() convenience function [#qt-api-load]
    - [x] get_task() wrapping matcher.find_task [#qt-api-get]
    - [x] Re-export add_task, update_status, list_tasks [#qt-api-reexport]
    - [x] Tests for API module [#qt-api-tests]
    - [x] CLI imports from API (thin wrapper) [#qt-api-cli]
- [x] improve README referencing a full manual in docs [#improve-readme]
## Backlog [#backlog]

- [x] Add link command for task and doc references [#link-cmd]
    - [x] qt link "Task B" --depends "Task A" for task dependencies
    - [x] qt link "Task" --doc "docs/design.md" to attach a doc reference
    - [x] qt link "Task" --doc "docs/plan.md#section" for doc section links
    - [x] Support multiple docs per task (docs metadata as comma-separated or list)
    - [x] Test: link creates depends metadata
    - [x] Test: link with bookmark reference
    - [x] Test: link --doc adds docs metadata
    - [x] Test: link --doc appends to existing docs
- [x] Add note command for task metadata [#note-cmd]
    - [x] CLI wiring: qt note "Task" "Some info"
    - [x] Test: note adds metadata to task
- [x] Add edit command to open file in $EDITOR [#edit-cmd]
    - [x] CLI wiring: qt edit "Task"
    - [x] Test: edit finds task and opens file
- [x] Add integration tests for full workflows [#integration-tests]
    - [x] Test: add -> start -> subtask -> done -> rollup
    - [x] Test: dependency linking workflow
    - [x] Test: doc linking and show workflow
- [x] Add show command to display single task detail [#show-cmd]
    - [x] Show title, status, bookmark, metadata, children
    - [x] Show linked docs and dependencies
    - [x] Support --json flag
- [x] Add remove command to delete tasks [#remove-cmd]
    - [x] Remove task and its children from file
    - [x] Test: remove top-level task
    - [x] Test: remove subtask
- [x] Add rename command to update task title [#rename-cmd]
    - [x] CLI wiring: qt rename "old" "new title"
    - [x] Test: rename preserves status and children
- [x] Improve list output formatting with Rich [#rich-output]
    - [x] Color-code statuses
    - [x] Show bookmark tags inline
    - [x] Show metadata counts
- [x] Add --verbose flag to list for showing metadata [#list-verbose]
- [x] Improve error messages for ambiguous matches [#ambiguous-errors]
    - [x] Show all matching tasks when query is ambiguous
    - [x] Suggest using bookmarks for precision
- [x] Add check command for task file validation [#check-cmd]
    - [x] Detect malformed task lines (near-miss patterns)
    - [x] Report unknown status symbols
    - [x] Find duplicate bookmarks
    - [x] Validate depends references point to existing tasks/bookmarks
    - [x] Detect orphaned metadata (key: value not under a task)
    - [x] Support --json flag for tooling integration
    - [x] Exit code 0 if clean, 1 if errors found
## quick-task Improvements [#qt-improvements]

- [x] Agent-oriented metadata fields [#qt-metadata]
    docs: docs/designs/qt-metadata.md, docs/designs/qt-metadata-tests.md
    updated: 2026-03-29T02:07:58Z
    - [x] Create metadata.py with constants and validation [#qt-metadata-module]
        updated: 2026-03-29T02:07:58Z
    - [x] Extend add_task() with assignee/priority params [#qt-metadata-add-task]
        updated: 2026-03-29T02:07:58Z
    - [x] Add set_metadata() to operations.py [#qt-metadata-set]
        updated: 2026-03-29T02:07:58Z
    - [x] CLI flags: --assignee, --priority on add and list [#qt-metadata-cli]
        updated: 2026-03-29T02:07:58Z
    - [x] Extend api.list_tasks() with assignee/priority filters [#qt-metadata-api]
        updated: 2026-03-29T02:07:58Z
    - [x] Tests for metadata, operations, CLI, and API [#qt-metadata-tests]
        updated: 2026-03-29T02:07:58Z
- [ ] Transition history / audit log [#qt-history]
    docs: spec/bootstrap-spec.md#transition-history
    - [ ] Append history metadata on status change [#qt-history-append]
    - [ ] qt show --history display [#qt-history-show]
    - [ ] JSON output includes history [#qt-history-json]
- [ ] File locking for concurrent access [#qt-locking]
    docs: spec/bootstrap-spec.md#file-locking
    - [ ] Advisory lock on write [#qt-lock-acquire]
    - [ ] Stale lock detection [#qt-lock-stale]
- [ ] Filter/query enhancements [#qt-filters]
    docs: spec/bootstrap-spec.md#filter-query
    - [ ] Compound filter support [#qt-filter-compound]
    - [ ] --has-metadata filter [#qt-filter-metadata]
## Done [#done]

- [x] Project setup
- [x] Data models (Task, TaskList, TaskFile, TaskStatus)
- [x] Markdown parser (flat, nested, metadata, bookmarks)
- [x] Markdown writer
- [x] Fuzzy matcher
- [x] Operations: add, update status, move, link dependency
- [x] File discovery
- [x] CLI: list command with status filter and JSON output
- [x] CLI: add command
- [x] CLI: status commands (done, start, block, defer, cancel, reset)
- [x] CLI: move command
- [x] CLI: init command with templates
- [x] README and usage documentation
