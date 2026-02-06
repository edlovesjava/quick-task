"""Tests for task file validation."""

from quick_task.checker import check_content


def test_valid_file_no_issues():
    content = """## Tasks

- [ ] First task
- [x] Done task
    - [ ] Subtask
"""
    issues = check_content(content)
    assert issues == []


def test_malformed_task_line():
    content = """## Tasks

- [] Missing space
- [ ] Valid task
"""
    issues = check_content(content)
    assert len(issues) == 1
    assert issues[0].code == "malformed-task"
    assert issues[0].line == 3


def test_unknown_status_symbol():
    content = """## Tasks

- [z] Bad status
"""
    issues = check_content(content)
    assert len(issues) == 1
    assert issues[0].code == "unknown-status"
    assert "z" in issues[0].message


def test_duplicate_bookmark():
    content = """## Tasks

- [ ] Task A [#dupe]
- [ ] Task B [#dupe]
"""
    issues = check_content(content)
    assert len(issues) == 1
    assert issues[0].code == "duplicate-bookmark"
    assert issues[0].line == 4


def test_duplicate_bookmark_header_and_task():
    content = """## Tasks [#dupe]

- [ ] Task A [#dupe]
"""
    issues = check_content(content)
    assert len(issues) == 1
    assert issues[0].code == "duplicate-bookmark"


def test_broken_depends_bookmark():
    content = """## Tasks

- [ ] Task A
    depends: #nonexistent
"""
    issues = check_content(content)
    assert any(i.code == "broken-depends" for i in issues)


def test_valid_depends_bookmark():
    content = """## Tasks

- [ ] Task A [#a]
- [ ] Task B
    depends: #a
"""
    issues = check_content(content)
    assert not any(i.code == "broken-depends" for i in issues)


def test_orphaned_metadata():
    content = """## Tasks

    key: value without a task
- [ ] Task A
"""
    issues = check_content(content)
    assert any(i.code == "orphaned-metadata" for i in issues)


def test_metadata_under_task_is_fine():
    content = """## Tasks

- [ ] Task A
    notes: This is fine
"""
    issues = check_content(content)
    assert not any(i.code == "orphaned-metadata" for i in issues)


def test_multiple_issues():
    content = """## Tasks

- [] Malformed
- [z] Bad status
- [ ] Task A [#dupe]
- [ ] Task B [#dupe]
    depends: #ghost
- [ ] Task C
    depends: #nonexistent
"""
    issues = check_content(content)
    codes = [i.code for i in issues]
    assert "malformed-task" in codes
    assert "unknown-status" in codes
    assert "duplicate-bookmark" in codes
    assert "broken-depends" in codes


def test_near_miss_no_space():
    content = """## Tasks

- [x]No space after bracket
"""
    issues = check_content(content)
    assert any(i.code == "malformed-task" for i in issues)
