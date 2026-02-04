"""CLI entry point for Quick Task."""

import click


@click.group()
@click.version_option()
def main():
    """Quick Task - Markdown-based task management."""
    pass


if __name__ == "__main__":
    main()
