## Backlog [#backlog]

- [ ] Add link command for task dependencies [#link-cmd]
    - [ ] CLI wiring: qt link "Task B" --depends "Task A"
    - [ ] Test: link creates depends metadata
    - [ ] Test: link with bookmark reference
- [ ] Add note command for task metadata [#note-cmd]
    - [ ] CLI wiring: qt note "Task" "Some info"
    - [ ] Test: note adds metadata to task
- [ ] Add edit command to open file in $EDITOR [#edit-cmd]
    - [ ] CLI wiring: qt edit "Task"
    - [ ] Test: edit finds task and opens file
- [ ] Add integration tests for full workflows [#integration-tests]
    - [ ] Test: add -> start -> subtask -> done -> rollup
    - [ ] Test: dependency linking workflow
- [ ] Add show command to display single task detail [#show-cmd]
    - [ ] Show title, status, bookmark, metadata, children
    - [ ] Support --json flag
- [ ] Add remove command to delete tasks [#remove-cmd]
    - [ ] Remove task and its children from file
    - [ ] Test: remove top-level task
    - [ ] Test: remove subtask
- [ ] Add rename command to update task title [#rename-cmd]
    - [ ] CLI wiring: qt rename "old" "new title"
    - [ ] Test: rename preserves status and children
- [ ] Improve list output formatting with Rich [#rich-output]
    - [ ] Color-code statuses
    - [ ] Show bookmark tags inline
    - [ ] Show metadata counts
- [ ] Add --verbose flag to list for showing metadata [#list-verbose]
- [ ] Improve error messages for ambiguous matches [#ambiguous-errors]
    - [ ] Show all matching tasks when query is ambiguous
    - [ ] Suggest using bookmarks for precision

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
