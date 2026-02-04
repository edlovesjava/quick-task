"""CLI entry point for Quick Task."""

import json

import click
from rich.console import Console
from rich.table import Table

from quick_task.discovery import find_task_file
from quick_task.parser import parse_file
from quick_task.models import TaskStatus
from quick_task.operations import add_task as op_add_task, update_status, move_task as op_move_task
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
@click.pass_context
def list_tasks(ctx, status, list_name, as_json):
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
            symbol = STATUS_SYMBOLS[t["status"]]
            indent = "  " * t["depth"]
            table.add_row(symbol, f"{indent}{t['task'].title}", t["list"])

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


if __name__ == "__main__":
    main()
