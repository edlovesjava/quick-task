"""Tests for file discovery."""

import os
import tempfile
from pathlib import Path

from quick_task.discovery import find_task_file, DEFAULT_FILENAME


def test_find_in_current_directory():
    with tempfile.TemporaryDirectory() as tmpdir:
        task_file = Path(tmpdir) / DEFAULT_FILENAME
        task_file.write_text("## Tasks\n")

        found = find_task_file(tmpdir)
        assert found == task_file


def test_find_walking_up():
    with tempfile.TemporaryDirectory() as tmpdir:
        task_file = Path(tmpdir) / DEFAULT_FILENAME
        task_file.write_text("## Tasks\n")

        subdir = Path(tmpdir) / "sub" / "deep"
        subdir.mkdir(parents=True)

        found = find_task_file(str(subdir))
        assert found == task_file


def test_returns_none_when_not_found():
    with tempfile.TemporaryDirectory() as tmpdir:
        found = find_task_file(tmpdir)
        assert found is None


def test_explicit_file_overrides():
    with tempfile.TemporaryDirectory() as tmpdir:
        explicit = Path(tmpdir) / "custom.md"
        explicit.write_text("## Tasks\n")

        found = find_task_file(tmpdir, explicit_file=str(explicit))
        assert found == explicit
