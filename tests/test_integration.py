"""Integration tests for full workflows."""

from pathlib import Path

from click.testing import CliRunner

from quick_task.cli import main


def test_full_workflow():
    """Add -> start -> subtask -> done -> rollup."""
    runner = CliRunner()
    with runner.isolated_filesystem():
        Path("TASKS.md").write_text("""## Backlog

## In Progress

## Done
""")

        # Add a task
        result = runner.invoke(main, ["add", "Build authentication", "--list", "Backlog"])
        assert result.exit_code == 0

        # Start the task
        result = runner.invoke(main, ["start", "Build auth"])
        assert result.exit_code == 0

        # Add subtasks
        result = runner.invoke(main, ["add", "Create login form", "--parent", "Build auth"])
        assert result.exit_code == 0
        result = runner.invoke(main, ["add", "Add validation", "--parent", "Build auth"])
        assert result.exit_code == 0

        # Complete subtasks — parent should auto-complete
        result = runner.invoke(main, ["done", "Create login"])
        assert result.exit_code == 0
        result = runner.invoke(main, ["done", "Add validation"])
        assert result.exit_code == 0

        content = Path("TASKS.md").read_text()
        assert "[x] Build authentication" in content

        # List as JSON
        result = runner.invoke(main, ["list", "--json"])
        assert result.exit_code == 0
        assert "Build authentication" in result.output


def test_dependency_workflow():
    """Link dependencies and verify metadata persists."""
    runner = CliRunner()
    with runner.isolated_filesystem():
        Path("TASKS.md").write_text("""## Tasks

- [ ] Set up database [#db]
- [ ] Build API
""")

        result = runner.invoke(main, ["link", "Build API", "--depends", "#db"])
        assert result.exit_code == 0

        content = Path("TASKS.md").read_text()
        assert "depends: #db" in content


def test_doc_linking_workflow():
    """Link docs and verify they render in list."""
    runner = CliRunner()
    with runner.isolated_filesystem():
        Path("TASKS.md").write_text("""## Tasks

- [ ] Auth system [#auth]
""")

        # Link a doc
        result = runner.invoke(main, ["link", "#auth", "--doc", "docs/design.md"])
        assert result.exit_code == 0

        # Link another doc
        result = runner.invoke(main, ["link", "#auth", "--doc", "docs/plan.md#auth-section"])
        assert result.exit_code == 0

        # Add a note
        result = runner.invoke(main, ["note", "#auth", "Using JWT tokens"])
        assert result.exit_code == 0

        content = Path("TASKS.md").read_text()
        assert "docs/design.md" in content
        assert "docs/plan.md#auth-section" in content
        assert "Using JWT tokens" in content


def test_move_and_reorder_workflow():
    """Add tasks, reorder, move between lists."""
    runner = CliRunner()
    with runner.isolated_filesystem():
        Path("TASKS.md").write_text("""## TODO

## Done
""")

        # Add tasks
        runner.invoke(main, ["add", "Task A", "--list", "TODO"])
        runner.invoke(main, ["add", "Task B", "--list", "TODO"])
        runner.invoke(main, ["add", "Task C", "--list", "TODO"])

        # Reorder: C before A
        result = runner.invoke(main, ["move", "Task C", "--before", "Task A"])
        assert result.exit_code == 0

        content = Path("TASKS.md").read_text()
        assert content.index("Task C") < content.index("Task A")

        # Complete and move to Done
        runner.invoke(main, ["done", "Task C"])
        result = runner.invoke(main, ["move", "Task C", "--list", "Done"])
        assert result.exit_code == 0

        content = Path("TASKS.md").read_text()
        done_idx = content.index("## Done")
        task_c_idx = content.index("Task C")
        assert task_c_idx > done_idx
