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
