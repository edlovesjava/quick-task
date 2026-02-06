"""Tests for CLI commands."""

import tempfile
from pathlib import Path

from click.testing import CliRunner

from quick_task.cli import main


def test_list_shows_tasks():
    runner = CliRunner()
    with runner.isolated_filesystem():
        Path("TASKS.md").write_text("""## Tasks

- [ ] First task
- [x] Done task
- [~] In progress
""")
        result = runner.invoke(main, ["list"])
        assert result.exit_code == 0
        assert "First task" in result.output
        assert "Done task" in result.output


def test_list_filter_by_status():
    runner = CliRunner()
    with runner.isolated_filesystem():
        Path("TASKS.md").write_text("""## Tasks

- [ ] Todo task
- [x] Done task
""")
        result = runner.invoke(main, ["list", "--status", "todo"])
        assert result.exit_code == 0
        assert "Todo task" in result.output
        assert "Done task" not in result.output


def test_list_json_output():
    runner = CliRunner()
    with runner.isolated_filesystem():
        Path("TASKS.md").write_text("""## Tasks

- [ ] My task
""")
        result = runner.invoke(main, ["list", "--json"])
        assert result.exit_code == 0
        assert '"title": "My task"' in result.output


def test_add_task():
    runner = CliRunner()
    with runner.isolated_filesystem():
        Path("TASKS.md").write_text("""## Tasks

- [ ] Existing task
""")
        result = runner.invoke(main, ["add", "New task"])
        assert result.exit_code == 0

        content = Path("TASKS.md").read_text()
        assert "New task" in content


def test_add_task_to_named_list():
    runner = CliRunner()
    with runner.isolated_filesystem():
        Path("TASKS.md").write_text("""## Backlog

## Done
""")
        result = runner.invoke(main, ["add", "New task", "--list", "Done"])
        assert result.exit_code == 0

        content = Path("TASKS.md").read_text()
        assert "Done" in content
        # Task should be under Done section


def test_add_subtask():
    runner = CliRunner()
    with runner.isolated_filesystem():
        Path("TASKS.md").write_text("""## Tasks

- [ ] Parent task
""")
        result = runner.invoke(main, ["add", "Child task", "--parent", "Parent"])
        assert result.exit_code == 0

        content = Path("TASKS.md").read_text()
        assert "Child task" in content


def test_done_command():
    runner = CliRunner()
    with runner.isolated_filesystem():
        Path("TASKS.md").write_text("""## Tasks

- [ ] My task
""")
        result = runner.invoke(main, ["done", "My task"])
        assert result.exit_code == 0

        content = Path("TASKS.md").read_text()
        assert "[x] My task" in content


def test_start_command():
    runner = CliRunner()
    with runner.isolated_filesystem():
        Path("TASKS.md").write_text("""## Tasks

- [ ] My task
""")
        result = runner.invoke(main, ["start", "My task"])
        assert result.exit_code == 0

        content = Path("TASKS.md").read_text()
        assert "[~] My task" in content


def test_block_command():
    runner = CliRunner()
    with runner.isolated_filesystem():
        Path("TASKS.md").write_text("""## Tasks

- [ ] My task
""")
        result = runner.invoke(main, ["block", "My task"])
        assert result.exit_code == 0

        content = Path("TASKS.md").read_text()
        assert "[?] My task" in content


def test_move_before():
    runner = CliRunner()
    with runner.isolated_filesystem():
        Path("TASKS.md").write_text("""## Tasks

- [ ] First
- [ ] Second
- [ ] Third
""")
        result = runner.invoke(main, ["move", "Third", "--before", "First"])
        assert result.exit_code == 0

        content = Path("TASKS.md").read_text()
        # Third should now be before First
        assert content.index("Third") < content.index("First")


def test_move_to_list():
    runner = CliRunner()
    with runner.isolated_filesystem():
        Path("TASKS.md").write_text("""## Todo

- [ ] My task

## Done
""")
        result = runner.invoke(main, ["move", "My task", "--list", "Done"])
        assert result.exit_code == 0

        content = Path("TASKS.md").read_text()
        # Task should be under Done now
        done_idx = content.index("## Done")
        task_idx = content.index("My task")
        assert task_idx > done_idx


def test_link_depends():
    runner = CliRunner()
    with runner.isolated_filesystem():
        Path("TASKS.md").write_text("""## Tasks

- [ ] Task A
- [ ] Task B
""")
        result = runner.invoke(main, ["link", "Task B", "--depends", "Task A"])
        assert result.exit_code == 0

        content = Path("TASKS.md").read_text()
        assert "depends: Task A" in content


def test_link_depends_with_bookmark():
    runner = CliRunner()
    with runner.isolated_filesystem():
        Path("TASKS.md").write_text("""## Tasks

- [ ] Task A [#a]
- [ ] Task B
""")
        result = runner.invoke(main, ["link", "Task B", "--depends", "#a"])
        assert result.exit_code == 0

        content = Path("TASKS.md").read_text()
        assert "depends: #a" in content


def test_link_doc():
    runner = CliRunner()
    with runner.isolated_filesystem():
        Path("TASKS.md").write_text("""## Tasks

- [ ] Auth system
""")
        result = runner.invoke(main, ["link", "Auth system", "--doc", "docs/auth-spec.md"])
        assert result.exit_code == 0

        content = Path("TASKS.md").read_text()
        assert "docs: docs/auth-spec.md" in content


def test_link_doc_appends():
    runner = CliRunner()
    with runner.isolated_filesystem():
        Path("TASKS.md").write_text("""## Tasks

- [ ] Auth system
    docs: docs/design.md
""")
        result = runner.invoke(main, ["link", "Auth system", "--doc", "docs/spec.md"])
        assert result.exit_code == 0

        content = Path("TASKS.md").read_text()
        assert "docs/design.md" in content
        assert "docs/spec.md" in content


def test_link_doc_with_section():
    runner = CliRunner()
    with runner.isolated_filesystem():
        Path("TASKS.md").write_text("""## Tasks

- [ ] Auth system
""")
        result = runner.invoke(main, ["link", "Auth system", "--doc", "docs/plan.md#cli-commands"])
        assert result.exit_code == 0

        content = Path("TASKS.md").read_text()
        assert "docs: docs/plan.md#cli-commands" in content


def test_note_command():
    runner = CliRunner()
    with runner.isolated_filesystem():
        Path("TASKS.md").write_text("""## Tasks

- [ ] My task
""")
        result = runner.invoke(main, ["note", "My task", "Some extra info"])
        assert result.exit_code == 0

        content = Path("TASKS.md").read_text()
        assert "notes: Some extra info" in content


def test_note_command_appends():
    runner = CliRunner()
    with runner.isolated_filesystem():
        Path("TASKS.md").write_text("""## Tasks

- [ ] My task
    notes: First note
""")
        result = runner.invoke(main, ["note", "My task", "Second note"])
        assert result.exit_code == 0

        content = Path("TASKS.md").read_text()
        assert "First note" in content
        assert "Second note" in content


def test_edit_opens_file(monkeypatch):
    runner = CliRunner()
    with runner.isolated_filesystem():
        Path("TASKS.md").write_text("""## Tasks

- [ ] My task
""")
        # Use 'true' as editor (no-op that exits 0)
        monkeypatch.setenv("EDITOR", "true")
        result = runner.invoke(main, ["edit"])
        assert result.exit_code == 0


def test_edit_with_query_validates_task(monkeypatch):
    runner = CliRunner()
    with runner.isolated_filesystem():
        Path("TASKS.md").write_text("""## Tasks

- [ ] My task
""")
        monkeypatch.setenv("EDITOR", "true")
        result = runner.invoke(main, ["edit", "--task", "nonexistent"])
        assert result.exit_code == 1
        assert "not found" in result.output.lower()


def test_show_task_detail():
    runner = CliRunner()
    with runner.isolated_filesystem():
        Path("TASKS.md").write_text("""## Tasks

- [~] Auth system [#auth]
    depends: #db
    docs: docs/design.md, docs/plan.md#auth
    notes: Using JWT tokens
    - [x] Create login form
    - [ ] Add validation
""")
        result = runner.invoke(main, ["show", "#auth"])
        assert result.exit_code == 0
        assert "Auth system" in result.output
        assert "#auth" in result.output
        assert "in-progress" in result.output.lower() or "in_progress" in result.output.lower()
        assert "docs/design.md" in result.output
        assert "Using JWT" in result.output
        assert "Create login form" in result.output


def test_show_task_json():
    runner = CliRunner()
    with runner.isolated_filesystem():
        Path("TASKS.md").write_text("""## Tasks

- [ ] My task [#my]
    docs: docs/spec.md
""")
        result = runner.invoke(main, ["show", "#my", "--json"])
        assert result.exit_code == 0
        import json
        data = json.loads(result.output)
        assert data["title"] == "My task"
        assert data["bookmark"] == "my"
        assert "docs/spec.md" in data["metadata"]["docs"]


def test_show_task_not_found():
    runner = CliRunner()
    with runner.isolated_filesystem():
        Path("TASKS.md").write_text("""## Tasks

- [ ] My task
""")
        result = runner.invoke(main, ["show", "nonexistent"])
        assert result.exit_code == 1


def test_remove_command():
    runner = CliRunner()
    with runner.isolated_filesystem():
        Path("TASKS.md").write_text("""## Tasks

- [ ] Task A
- [ ] Task B
""")
        result = runner.invoke(main, ["remove", "Task A"])
        assert result.exit_code == 0

        content = Path("TASKS.md").read_text()
        assert "Task A" not in content
        assert "Task B" in content


def test_remove_subtask_command():
    runner = CliRunner()
    with runner.isolated_filesystem():
        Path("TASKS.md").write_text("""## Tasks

- [ ] Parent
    - [ ] Child A
    - [ ] Child B
""")
        result = runner.invoke(main, ["remove", "Child A"])
        assert result.exit_code == 0

        content = Path("TASKS.md").read_text()
        assert "Child A" not in content
        assert "Parent" in content
        assert "Child B" in content


def test_rename_command():
    runner = CliRunner()
    with runner.isolated_filesystem():
        Path("TASKS.md").write_text("""## Tasks

- [~] Old name [#t]
    - [ ] Child
""")
        result = runner.invoke(main, ["rename", "Old name", "New name"])
        assert result.exit_code == 0

        content = Path("TASKS.md").read_text()
        assert "New name" in content
        assert "Old name" not in content
        assert "[#t]" in content
        assert "Child" in content


def test_list_verbose():
    runner = CliRunner()
    with runner.isolated_filesystem():
        Path("TASKS.md").write_text("""## Tasks

- [ ] My task [#my]
    docs: docs/spec.md
    notes: Important info
""")
        result = runner.invoke(main, ["list", "--verbose"])
        assert result.exit_code == 0
        assert "docs/spec.md" in result.output
        assert "Important info" in result.output


def test_init_creates_default_file():
    """init creates TASKS.md with default template."""
    runner = CliRunner()
    with runner.isolated_filesystem():
        result = runner.invoke(main, ["init"])
        assert result.exit_code == 0

        assert Path("TASKS.md").exists()
        content = Path("TASKS.md").read_text()
        assert "## Tasks" in content


def test_init_kanban_template():
    """init --template kanban creates kanban-style file."""
    runner = CliRunner()
    with runner.isolated_filesystem():
        result = runner.invoke(main, ["init", "--template", "kanban"])
        assert result.exit_code == 0

        content = Path("TASKS.md").read_text()
        assert "## TODO" in content
        assert "## In Progress" in content
        assert "## Done" in content


def test_init_refuses_if_file_exists():
    """init refuses to overwrite existing file."""
    runner = CliRunner()
    with runner.isolated_filesystem():
        Path("TASKS.md").write_text("existing content")
        result = runner.invoke(main, ["init"])
        assert result.exit_code == 1
        assert "already exists" in result.output

        # File unchanged
        assert Path("TASKS.md").read_text() == "existing content"


def test_init_force_overwrites():
    """init --force overwrites existing file."""
    runner = CliRunner()
    with runner.isolated_filesystem():
        Path("TASKS.md").write_text("existing content")
        result = runner.invoke(main, ["init", "--force"])
        assert result.exit_code == 0

        content = Path("TASKS.md").read_text()
        assert "## Tasks" in content
        assert "existing content" not in content
