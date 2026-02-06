"""CLI entry point for Quick Task."""

import json
import os
import subprocess
from pathlib import Path

import click
from rich.console import Console
from rich.table import Table

from quick_task.discovery import find_task_file
from quick_task.parser import parse_file
from quick_task.models import TaskStatus
from quick_task.matcher import find_task
from quick_task.checker import check_file
from quick_task.operations import add_task as op_add_task, update_status, move_task as op_move_task, link_dependency, link_doc, remove_task as op_remove_task, rename_task as op_rename_task
from quick_task.writer import write_file


console = Console()

STATUS_SYMBOLS = {
    TaskStatus.TODO: "[ ]",
    TaskStatus.IN_PROGRESS: "[~]",
    TaskStatus.DONE: "[x]",
    TaskStatus.CANCELLED: "[-]",
    TaskStatus.BLOCKED: "[?]",
    TaskStatus.DEFERRED: "[>]",
}

STATUS_STYLES = {
    TaskStatus.TODO: "white",
    TaskStatus.IN_PROGRESS: "cyan",
    TaskStatus.DONE: "green",
    TaskStatus.CANCELLED: "dim",
    TaskStatus.BLOCKED: "red",
    TaskStatus.DEFERRED: "yellow",
}

STATUS_NAMES = {
    "todo": TaskStatus.TODO,
    "in-progress": TaskStatus.IN_PROGRESS,
    "done": TaskStatus.DONE,
    "cancelled": TaskStatus.CANCELLED,
    "blocked": TaskStatus.BLOCKED,
    "deferred": TaskStatus.DEFERRED,
}


@click.group()
@click.version_option()
@click.option("--file", "-f", "file_path", help="Task file to use")
@click.pass_context
def main(ctx, file_path):
    """Quick Task - Markdown-based task management."""
    ctx.ensure_object(dict)
    ctx.obj["file_path"] = file_path


@main.command("list")
@click.option(
    "--status", "-s",
    type=click.Choice(["todo", "in-progress", "done", "cancelled", "blocked", "deferred"], case_sensitive=False),
    help="Filter by status",
)
@click.option("--list", "-l", "list_name", help="Filter by list name")
@click.option("--json", "as_json", is_flag=True, help="Output as JSON")
@click.option("--verbose", "-v", is_flag=True, help="Show metadata")
@click.pass_context
def list_tasks(ctx, status, list_name, as_json, verbose):
    """List tasks."""
    file_path = find_task_file(explicit_file=ctx.obj.get("file_path"))
    if not file_path:
        console.print("[red]No task file found[/red]")
        raise SystemExit(1)

    task_file = parse_file(file_path)

    # Collect tasks
    tasks = []
    for tl in task_file.lists:
        if list_name and tl.name.lower() != list_name.lower():
            continue
        for task in collect_with_list(tl.name, tl.tasks, 0):
            tasks.append(task)

    # Filter by status
    if status:
        target_status = STATUS_NAMES.get(status.lower())
        tasks = [t for t in tasks if t["status"] == target_status]

    if as_json:
        output = [
            {
                "title": t["task"].title,
                "status": t["status"].name.lower(),
                "list": t["list"],
                "bookmark": t["task"].bookmark,
            }
            for t in tasks
        ]
        click.echo(json.dumps(output, indent=2))
    else:
        table = Table(show_header=True)
        table.add_column("Status", width=5)
        table.add_column("Task")
        table.add_column("List")

        for t in tasks:
            status = t["status"]
            style = STATUS_STYLES[status]
            symbol = STATUS_SYMBOLS[status]
            indent = "  " * t["depth"]
            task_text = f"{indent}{t['task'].title}"
            if t["task"].bookmark:
                task_text += f" [dim]\\[#{t['task'].bookmark}][/dim]"
            if not verbose:
                meta_count = len(t["task"].metadata)
                if meta_count:
                    task_text += f" [dim]({meta_count} meta)[/dim]"
            if verbose and t["task"].metadata:
                for key, value in t["task"].metadata.items():
                    task_text += f"\n{indent}  [dim]{key}: {value}[/dim]"
            table.add_row(f"[{style}]{symbol}[/{style}]", task_text, t["list"])

        console.print(table)


def collect_with_list(list_name, tasks, depth):
    """Collect tasks with their list name and depth."""
    for task in tasks:
        yield {"task": task, "status": task.status, "list": list_name, "depth": depth}
        yield from collect_with_list(list_name, task.children, depth + 1)


@main.command("add")
@click.argument("title")
@click.option("--list", "-l", "list_name", help="Target list name")
@click.option("--parent", "-p", "parent_query", help="Parent task (creates subtask)")
@click.pass_context
def add(ctx, title, list_name, parent_query):
    """Add a new task."""
    file_path = find_task_file(explicit_file=ctx.obj.get("file_path"))
    if not file_path:
        console.print("[red]No task file found[/red]")
        raise SystemExit(1)

    task_file = parse_file(file_path)

    try:
        task = op_add_task(task_file, title, list_name=list_name, parent_query=parent_query)
        write_file(task_file)
        console.print(f"[green]Added:[/green] {task.title}")
    except Exception as e:
        console.print(f"[red]Error:[/red] {e}")
        raise SystemExit(1)


@main.command("move")
@click.argument("query")
@click.option("--before", "-b", help="Move before this task")
@click.option("--after", "-a", help="Move after this task")
@click.option("--list", "-l", "to_list", help="Move to this list")
@click.pass_context
def move(ctx, query, before, after, to_list):
    """Move a task to a new position or list."""
    file_path = find_task_file(explicit_file=ctx.obj.get("file_path"))
    if not file_path:
        console.print("[red]No task file found[/red]")
        raise SystemExit(1)

    task_file = parse_file(file_path)

    try:
        task = op_move_task(task_file, query, before=before, after=after, to_list=to_list)
        write_file(task_file)
        console.print(f"[green]Moved:[/green] {task.title}")
    except Exception as e:
        console.print(f"[red]Error:[/red] {e}")
        raise SystemExit(1)


@main.command("check")
@click.option("--json", "as_json", is_flag=True, help="Output as JSON")
@click.pass_context
def check(ctx, as_json):
    """Validate the task file for errors."""
    file_path = find_task_file(explicit_file=ctx.obj.get("file_path"))
    if not file_path:
        console.print("[red]No task file found[/red]")
        raise SystemExit(1)

    issues = check_file(file_path)

    if as_json:
        output = [
            {"line": i.line, "level": i.level, "code": i.code, "message": i.message}
            for i in issues
        ]
        click.echo(json.dumps(output, indent=2))
    elif issues:
        for issue in issues:
            level_style = "red" if issue.level == "error" else "yellow"
            console.print(f"[{level_style}]{issue.level}[/{level_style}] line {issue.line}: {issue.message}")
    else:
        console.print("[green]No issues found[/green]")

    if any(i.level == "error" for i in issues):
        raise SystemExit(1)


@main.command("rename")
@click.argument("query")
@click.argument("new_title")
@click.pass_context
def rename(ctx, query, new_title):
    """Rename a task."""
    file_path = find_task_file(explicit_file=ctx.obj.get("file_path"))
    if not file_path:
        console.print("[red]No task file found[/red]")
        raise SystemExit(1)

    task_file = parse_file(file_path)

    try:
        task = op_rename_task(task_file, query, new_title)
        write_file(task_file)
        console.print(f"[green]Renamed:[/green] {task.title}")
    except Exception as e:
        console.print(f"[red]Error:[/red] {e}")
        raise SystemExit(1)


@main.command("remove")
@click.argument("query")
@click.pass_context
def remove(ctx, query):
    """Remove a task."""
    file_path = find_task_file(explicit_file=ctx.obj.get("file_path"))
    if not file_path:
        console.print("[red]No task file found[/red]")
        raise SystemExit(1)

    task_file = parse_file(file_path)

    try:
        title = op_remove_task(task_file, query)
        write_file(task_file)
        console.print(f"[green]Removed:[/green] {title}")
    except Exception as e:
        console.print(f"[red]Error:[/red] {e}")
        raise SystemExit(1)


@main.command("show")
@click.argument("query")
@click.option("--json", "as_json", is_flag=True, help="Output as JSON")
@click.pass_context
def show(ctx, query, as_json):
    """Show detail for a single task."""
    file_path = find_task_file(explicit_file=ctx.obj.get("file_path"))
    if not file_path:
        console.print("[red]No task file found[/red]")
        raise SystemExit(1)

    task_file = parse_file(file_path)
    task = find_task(task_file, query)
    if task is None:
        console.print(f"[red]Task not found:[/red] {query}")
        raise SystemExit(1)

    if as_json:
        data = task_to_dict(task)
        click.echo(json.dumps(data, indent=2))
    else:
        symbol = STATUS_SYMBOLS[task.status]
        title_line = f"{symbol} {task.title}"
        if task.bookmark:
            title_line += f" [#{task.bookmark}]"
        console.print(title_line)
        console.print(f"Status: {task.status.name.lower()}")
        if task.metadata:
            for key, value in task.metadata.items():
                console.print(f"{key}: {value}")
        if task.children:
            console.print("Subtasks:")
            for child in task.children:
                child_symbol = STATUS_SYMBOLS[child.status]
                console.print(f"  {child_symbol} {child.title}")


def task_to_dict(task):
    """Convert a task to a JSON-serializable dict."""
    data = {
        "title": task.title,
        "status": task.status.name.lower(),
        "bookmark": task.bookmark,
        "metadata": dict(task.metadata),
        "children": [task_to_dict(c) for c in task.children],
    }
    return data


@main.command("link")
@click.argument("query")
@click.option("--depends", "-d", "depends_on", help="Task this depends on")
@click.option("--doc", "doc_path", help="Doc path to link (e.g. docs/spec.md or docs/plan.md#section)")
@click.pass_context
def link(ctx, query, depends_on, doc_path):
    """Link a task to a dependency or document."""
    if not depends_on and not doc_path:
        console.print("[red]Error:[/red] Provide --depends or --doc")
        raise SystemExit(1)

    file_path = find_task_file(explicit_file=ctx.obj.get("file_path"))
    if not file_path:
        console.print("[red]No task file found[/red]")
        raise SystemExit(1)

    task_file = parse_file(file_path)

    try:
        if depends_on:
            task = link_dependency(task_file, query, depends_on)
            write_file(task_file)
            console.print(f"[green]Linked:[/green] {task.title} depends on {depends_on}")
        if doc_path:
            task = link_doc(task_file, query, doc_path)
            write_file(task_file)
            console.print(f"[green]Linked:[/green] {task.title} -> {doc_path}")
    except Exception as e:
        console.print(f"[red]Error:[/red] {e}")
        raise SystemExit(1)


@main.command("note")
@click.argument("query")
@click.argument("text")
@click.pass_context
def note(ctx, query, text):
    """Add a note to a task."""
    file_path = find_task_file(explicit_file=ctx.obj.get("file_path"))
    if not file_path:
        console.print("[red]No task file found[/red]")
        raise SystemExit(1)

    task_file = parse_file(file_path)

    try:
        task = find_task(task_file, query)
        if task is None:
            console.print(f"[red]Task not found:[/red] {query}")
            raise SystemExit(1)
        existing = task.metadata.get("notes", "")
        if existing:
            task.metadata["notes"] = f"{existing}; {text}"
        else:
            task.metadata["notes"] = text
        write_file(task_file)
        console.print(f"[green]Added note to:[/green] {task.title}")
    except SystemExit:
        raise
    except Exception as e:
        console.print(f"[red]Error:[/red] {e}")
        raise SystemExit(1)


@main.command("edit")
@click.option("--task", "-t", "query", help="Task to find in the file")
@click.pass_context
def edit(ctx, query):
    """Open the task file in $EDITOR."""
    file_path = find_task_file(explicit_file=ctx.obj.get("file_path"))
    if not file_path:
        console.print("[red]No task file found[/red]")
        raise SystemExit(1)

    if query:
        task_file = parse_file(file_path)
        task = find_task(task_file, query)
        if task is None:
            console.print(f"[red]Task not found:[/red] {query}")
            raise SystemExit(1)

    editor = os.environ.get("EDITOR", "vi")
    subprocess.run([editor, str(file_path)])


def make_status_command(name, status, verb, past_tense):
    """Factory for status update commands."""

    @main.command(name, help=f"{verb} a task.")
    @click.argument("query")
    @click.option("--force", is_flag=True, help="Force even with incomplete dependencies")
    @click.pass_context
    def command(ctx, query, force):
        file_path = find_task_file(explicit_file=ctx.obj.get("file_path"))
        if not file_path:
            console.print("[red]No task file found[/red]")
            raise SystemExit(1)

        task_file = parse_file(file_path)

        try:
            task = update_status(task_file, query, status, force=force)
            write_file(task_file)
            console.print(f"[green]{past_tense}:[/green] {task.title}")
        except Exception as e:
            console.print(f"[red]Error:[/red] {e}")
            raise SystemExit(1)

    return command


# Register status commands
done = make_status_command("done", TaskStatus.DONE, "Mark complete", "Completed")
start = make_status_command("start", TaskStatus.IN_PROGRESS, "Mark in-progress", "Started")
block = make_status_command("block", TaskStatus.BLOCKED, "Mark blocked", "Blocked")
defer = make_status_command("defer", TaskStatus.DEFERRED, "Mark deferred", "Deferred")
cancel = make_status_command("cancel", TaskStatus.CANCELLED, "Mark cancelled", "Cancelled")
reset = make_status_command("reset", TaskStatus.TODO, "Reset to todo", "Reset")


TEMPLATES = {
    "simple": """## Tasks

- [ ] First task
""",
    "kanban": """## TODO [#todo]

## In Progress [#wip]

## Done [#done]
""",
}


@main.command("init")
@click.option(
    "--template", "-t",
    type=click.Choice(["simple", "kanban"], case_sensitive=False),
    default="simple",
    help="Template to use",
)
@click.option("--force", is_flag=True, help="Overwrite existing file")
def init(template, force):
    """Initialize a new TASKS.md file."""
    path = Path("TASKS.md")

    if path.exists() and not force:
        console.print("[red]TASKS.md already exists[/red] (use --force to overwrite)")
        raise SystemExit(1)

    content = TEMPLATES[template.lower()]
    path.write_text(content)
    console.print(f"[green]Created TASKS.md[/green] ({template} template)")


if __name__ == "__main__":
    main()
